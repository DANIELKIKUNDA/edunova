import 'cloud_sync_repository.dart';
import '../domain/cloud_sync.dart';

class RunCloudSync {
  RunCloudSync({
    required this.local,
    required this.remote,
    required this.accountIdProvider,
    required this.platform,
    required this.deviceName,
    required this.appVersion,
  });
  final CloudSyncLocalRepository local;
  final CloudSyncRemoteGateway remote;
  final Future<String?> Function() accountIdProvider;
  final String platform;
  final String deviceName;
  final String appVersion;

  // Share one in-flight run between simultaneous UI/background triggers.
  // Otherwise both runs can read and push the same outbox before either
  // records its acknowledgement.
  Future<SyncRunResult>? _inFlight;

  Future<SyncRunResult> call() {
    final running = _inFlight;
    if (running != null) return running;
    final future = _run();
    _inFlight = future;
    future.whenComplete(() {
      if (identical(_inFlight, future)) _inFlight = null;
    }).ignore();
    return future;
  }

  // A logout/account switch during an awaited network call must not commit
  // the previous account's remote payload into shared local projections.
  Future<void> _assertAccount(String expected) async {
    if (await accountIdProvider() != expected) {
      throw StateError('sync_account_changed');
    }
  }

  Future<SyncRunResult> _run() async {
    final accountId = await accountIdProvider();
    if (accountId == null || accountId.isEmpty) throw StateError('authentication_required');
    final state = await local.ensureState(accountId);
    var cursor = state.serverCursor;
    var pushed = 0;
    var pulled = 0;
    var conflicts = 0;
    try {
      if (!state.registered) {
        await remote.registerDevice(deviceId: state.deviceId, name: deviceName, platform: platform, appVersion: appVersion);
        await _assertAccount(accountId);
        await local.markRegistered(accountId);
      }

      final pending = await local.pendingMutations(accountId, limit: 100);
      if (pending.isNotEmpty) {
        final outcomes = await remote.push(deviceId: state.deviceId, mutations: pending);
        final byId = {for (final m in pending) m.id: m};
        // A partial or malformed server response must not be treated as a
        // successful push: otherwise the subsequent pull/ack can hide unsent
        // local changes. Keep the outbox intact and retry safely.
        final receivedIds = <String>{};
        for (final outcome in outcomes) {
          if (!byId.containsKey(outcome.mutationId) ||
              !receivedIds.add(outcome.mutationId)) {
            throw StateError('invalid_push_outcomes');
          }
        }
        if (receivedIds.length != pending.length) {
          throw StateError('incomplete_push_outcomes');
        }
        // Validate every disposition before touching the local outbox. A malformed
        // outcome at the end of the batch must not partially acknowledge earlier
        // mutations; the entire batch is retried with the same mutation IDs.
        for (final outcome in outcomes) {
          final mutation = byId[outcome.mutationId]!;
          // A provider response must never apply a canonical record belonging
          // to another entity. Validate both successful and conflict payloads.
          for (final record in <CloudRecord?>[outcome.record, outcome.canonical]) {
            if (record == null) continue;
            if (record.entityType != mutation.entityType ||
                record.entityId != mutation.entityId ||
                record.version < 1 || record.serverSeq < 0) {
              throw StateError('invalid_push_record');
            }
          }
          if (outcome.disposition == 'conflict' && outcome.canonical == null) {
            throw StateError('missing_canonical_conflict');
          }
          if (outcome.disposition != 'applied' &&
              outcome.disposition != 'duplicate' &&
              outcome.disposition != 'conflict' &&
              outcome.disposition != 'rejected') {
            throw StateError('unknown_push_disposition');
          }
        }
        await _assertAccount(accountId);
        await local.applyPushOutcomes(accountId, pending, outcomes);
        pushed += outcomes.where((o) => o.disposition == 'applied' || o.disposition == 'duplicate').length;
        conflicts += outcomes.where((o) => o.disposition == 'conflict').length;
      }

      if (cursor == 0) {
        final snapshot = await remote.bootstrap(deviceId: state.deviceId);
        _validateSnapshot(snapshot);
        await _assertAccount(accountId);
        await local.applyCanonicalPage(accountId, snapshot.changes, snapshot.nextCursor,
            retainedFloor: snapshot.retainedFloor, bootstrappedAt: DateTime.now().toUtc());
        pulled += snapshot.changes.length;
        cursor = snapshot.nextCursor;
      }

      var pages = 0;
      var hasMore = true;
      while (hasMore && pages < 5) {
        final page = await remote.pull(deviceId: state.deviceId, cursor: cursor, limit: 200);
        if (page.resetRequired) {
          // The server safely compacted history that this device had not acknowledged.
          // Reconcile against the canonical snapshot instead of replaying an incomplete delta stream.
          // Fetch and validate the full canonical snapshot *before* clearing
          // synchronized local state. A failed network request or malformed
          // snapshot must leave the existing offline library intact.
          final snapshot = await remote.bootstrap(deviceId: state.deviceId);
          _validateSnapshot(snapshot);
          await _assertAccount(accountId);
        await local.applyCanonicalPage(accountId, snapshot.changes, snapshot.nextCursor,
              retainedFloor: snapshot.retainedFloor, reset: true,
              bootstrappedAt: DateTime.now().toUtc());
          pulled += snapshot.changes.length;
          cursor = snapshot.nextCursor;
          hasMore = false;
          break;
        }
        // A regressing cursor could silently replay or lose changes. Validate
        // before applying any records or advancing the local checkpoint.
        if (page.nextCursor < cursor ||
            (page.hasMore && page.nextCursor == cursor)) {
          throw StateError('invalid_pull_cursor');
        }
        _validateDelta(page, cursor);
        await _assertAccount(accountId);
        await local.applyCanonicalPage(accountId, page.changes, page.nextCursor,
            retainedFloor: page.retainedFloor);
        pulled += page.changes.length;
        cursor = page.nextCursor;
        hasMore = page.hasMore;
        pages++;
      }

      final acked = await remote.acknowledge(deviceId: state.deviceId, cursor: cursor);
      if (acked < 0 || acked > cursor || acked < state.ackedCursor) {
        throw StateError('invalid_ack_cursor');
      }
      await _assertAccount(accountId);
      await local.markAcknowledged(accountId, acked);
      await _assertAccount(accountId);
      await local.updateCursor(accountId, cursor, syncedAt: DateTime.now().toUtc());
      return SyncRunResult(pushed: pushed, pulled: pulled, conflicts: conflicts, cursor: cursor);
    } catch (error) {
      if (await accountIdProvider() == accountId) {
        await local.recordSyncError(accountId, error.toString());
      }
      rethrow;
    }
  }

  // Validate the complete remote batch before applying any records. The
  // server cursor is an inclusive upper bound on records in that batch.
  void _validateSnapshot(PullPage page) {
    if (page.nextCursor < 0 || page.retainedFloor < 0 ||
        page.retainedFloor > page.nextCursor || page.resetRequired || page.hasMore) {
      throw StateError('invalid_bootstrap_page');
    }
    final seen = <String>{};
    for (final record in page.changes) {
      if (!seen.add('${record.entityType}:${record.entityId}')) {
        throw StateError('duplicate_bootstrap_entity');
      }
      if (record.serverSeq < 0 || record.serverSeq > page.nextCursor ||
          record.version < 1) {
        throw StateError('invalid_bootstrap_record');
      }
    }
  }

  void _validateDelta(PullPage page, int cursor) {
    if (page.nextCursor < 0 || page.retainedFloor < 0 ||
        page.retainedFloor > page.nextCursor) {
      throw StateError('invalid_pull_page');
    }
    // Delta streams must be strictly ordered. Applying a duplicated or
    // out-of-order sequence can overwrite a newer local canonical record.
    var previousSeq = cursor;
    for (final record in page.changes) {
      if (record.serverSeq <= previousSeq ||
          record.serverSeq > page.nextCursor || record.version < 1) {
        throw StateError('invalid_pull_record');
      }
      previousSeq = record.serverSeq;
    }
  }

}

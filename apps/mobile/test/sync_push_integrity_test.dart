import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:edunova/src/features/sync/application/run_cloud_sync.dart';
import 'package:edunova/src/features/sync/application/cloud_sync_repository.dart';
import 'package:edunova/src/features/sync/domain/cloud_sync.dart';

class _Local implements CloudSyncLocalRepository {
  int applied = 0;
  int pulls = 0;
  String? error;
  @override
  Future<CloudSyncState> ensureState(String accountId) async => const CloudSyncState(
    deviceId: 'device', serverCursor: 1, ackedCursor: 1,
    retainedFloor: 0, registered: true,
  );
  @override
  Future<List<CloudMutation>> pendingMutations(String accountId, {int limit = 100}) async => emptyPending ? [] : [
    CloudMutation(id: 'a', entityType: 'progress', entityId: '1', operation: 'upsert',
      payload: const {}, clientModifiedAt: DateTime.utc(2026)),
    CloudMutation(id: 'b', entityType: 'progress', entityId: '2', operation: 'upsert',
      payload: const {}, clientModifiedAt: DateTime.utc(2026)),
  ];
  bool emptyPending = false;
  @override
  Future<void> updateCursor(String accountId, int cursor,
      {int? retainedFloor, DateTime? syncedAt, DateTime? bootstrappedAt, String? lastError}) async {
    error = lastError;
  }
  @override
  Future<void> recordSyncError(String accountId, String error) =>
      updateCursor(accountId, 1, lastError: error);
  @override
  Future<void> applyCanonicalPage(String accountId, List<CloudRecord> records, int cursor,
      {required int retainedFloor, bool reset = false, DateTime? bootstrappedAt}) async {}
  @override
  Future<void> applyPushOutcomes(String accountId, List<CloudMutation> mutations, List<PushOutcome> outcomes) async {
    final byId = {for (final mutation in mutations) mutation.id: mutation};
    for (final outcome in outcomes) {
      final mutation = byId[outcome.mutationId]!;
      switch (outcome.disposition) {
        case 'applied':
        case 'duplicate':
          await markMutationApplied(accountId, mutation.id, outcome.record);
          break;
        case 'conflict':
          await storeConflict(accountId, mutation, outcome.canonical!, outcome.reason ?? 'conflict');
          await applyRemoteRecord(accountId, outcome.canonical!);
          break;
        case 'rejected':
          await markMutationFailed(accountId, mutation.id, outcome.reason ?? 'rejected');
          break;
      }
    }
  }

  @override
  Future<void> markMutationApplied(String accountId, String mutationId, CloudRecord? record) async { applied++; }
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _Remote implements CloudSyncRemoteGateway {
  _Remote(this.outcomes, {this.pushGate});
  final List<PushOutcome> outcomes;
  int pulls = 0;
  int pushes = 0;
  final Completer<void>? pushGate;
  PullPage? pullResult;
  @override
  Future<List<PushOutcome>> push({required String deviceId, required List<CloudMutation> mutations}) async {
    pushes++;
    if (pushGate != null) await pushGate!.future;
    return outcomes;
  }
  @override
  Future<PullPage> pull({required String deviceId, required int cursor, int limit = 200}) async {
    pulls++;
    return pullResult ?? PullPage(changes: const [], nextCursor: cursor, hasMore: false);
  }
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  Future<void> verifyRejected(List<PushOutcome> outcomes, String expected) async {
    final local = _Local();
    final remote = _Remote(outcomes);
    final runner = RunCloudSync(local: local, remote: remote,
      accountIdProvider: () async => 'account', platform: 'android',
      deviceName: 'test', appVersion: 'test');
    await expectLater(runner(), throwsA(isA<StateError>().having(
      (e) => e.message, 'message', expected)));
    expect(local.applied, 0);
    expect(remote.pulls, 0);
    expect(local.error, contains(expected));
  }
  test('late unknown disposition never partially acknowledges outbox', () async {
    await verifyRejected([
      const PushOutcome(mutationId: 'a', disposition: 'applied'),
      const PushOutcome(mutationId: 'b', disposition: 'unexpected'),
    ], 'unknown_push_disposition');
  });
  test('late conflict without canonical never partially acknowledges outbox', () async {
    await verifyRejected([
      const PushOutcome(mutationId: 'a', disposition: 'applied'),
      const PushOutcome(mutationId: 'b', disposition: 'conflict'),
    ], 'missing_canonical_conflict');
  });
  test('mismatched successful canonical record cannot modify another entity', () async {
    await verifyRejected([
      PushOutcome(mutationId: 'a', disposition: 'applied', record: CloudRecord(
        entityType: 'progress', entityId: '2', version: 1, serverSeq: 3,
        payload: const {}, deleted: false, updatedAt: DateTime.utc(2026))),
      const PushOutcome(mutationId: 'b', disposition: 'applied'),
    ], 'invalid_push_record');
  });
  test('mismatched conflict canonical record is rejected before writes', () async {
    await verifyRejected([
      const PushOutcome(mutationId: 'a', disposition: 'applied'),
      PushOutcome(mutationId: 'b', disposition: 'conflict', canonical: CloudRecord(
        entityType: 'progress', entityId: '1', version: 1, serverSeq: 3,
        payload: const {}, deleted: false, updatedAt: DateTime.utc(2026))),
    ], 'invalid_push_record');
  });
  test('invalid canonical version is rejected before writes', () async {
    await verifyRejected([
      PushOutcome(mutationId: 'a', disposition: 'duplicate', record: CloudRecord(
        entityType: 'progress', entityId: '1', version: 0, serverSeq: 3,
        payload: const {}, deleted: false, updatedAt: DateTime.utc(2026))),
      const PushOutcome(mutationId: 'b', disposition: 'applied'),
    ], 'invalid_push_record');
  });
  test('regressing pull cursor is rejected before acknowledgement', () async {
    final local = _Local()..emptyPending = true;
    final remote = _Remote([])..pullResult = const PullPage(changes: [], nextCursor: 0, hasMore: false);
    final runner = RunCloudSync(local: local, remote: remote,
      accountIdProvider: () async => 'account', platform: 'android', deviceName: 'test', appVersion: 'test');
    await expectLater(runner(), throwsA(isA<StateError>().having(
      (e) => e.message, 'message', 'invalid_pull_cursor')));
    expect(local.error, contains('invalid_pull_cursor'));
  });
  test('non-progressing paginated pull cursor is rejected', () async {
    final local = _Local()..emptyPending = true;
    final remote = _Remote([])..pullResult = const PullPage(changes: [], nextCursor: 1, hasMore: true);
    final runner = RunCloudSync(local: local, remote: remote,
      accountIdProvider: () async => 'account', platform: 'android', deviceName: 'test', appVersion: 'test');
    await expectLater(runner(), throwsA(isA<StateError>().having(
      (e) => e.message, 'message', 'invalid_pull_cursor')));
  });
  test('missing push outcome blocks pull and keeps outbox', () async {
    await verifyRejected([const PushOutcome(mutationId: 'a', disposition: 'applied')], 'incomplete_push_outcomes');
  });
  test('duplicate push outcome blocks pull and keeps outbox', () async {
    await verifyRejected([
      const PushOutcome(mutationId: 'a', disposition: 'applied'),
      const PushOutcome(mutationId: 'a', disposition: 'applied'),
    ], 'invalid_push_outcomes');
  });
  test('unknown push outcome blocks pull and keeps outbox', () async {
    await verifyRejected([
      const PushOutcome(mutationId: 'a', disposition: 'applied'),
      const PushOutcome(mutationId: 'unknown', disposition: 'applied'),
    ], 'invalid_push_outcomes');
  });
  test('account switch during push cannot commit old account outcomes', () async {
    final gate = Completer<void>();
    final local = _Local();
    final remote = _Remote([
      const PushOutcome(mutationId: 'a', disposition: 'applied'),
      const PushOutcome(mutationId: 'b', disposition: 'applied'),
    ], pushGate: gate);
    var currentAccount = 'account-a';
    final runner = RunCloudSync(local: local, remote: remote,
      accountIdProvider: () async => currentAccount, platform: 'android',
      deviceName: 'test', appVersion: 'test');
    final pending = runner();
    await Future<void>.delayed(const Duration(milliseconds: 10));
    currentAccount = 'account-b';
    gate.complete();
    await expectLater(pending, throwsA(isA<StateError>().having(
      (e) => e.message, 'message', 'sync_account_changed')));
    expect(local.applied, 0);
    expect(remote.pulls, 0);
    expect(local.error, isNull);
  });

  test('simultaneous triggers share a single push and release lock after failure', () async {
    final gate = Completer<void>();
    final local = _Local();
    final remote = _Remote([
      const PushOutcome(mutationId: 'a', disposition: 'unexpected'),
      const PushOutcome(mutationId: 'b', disposition: 'applied'),
    ], pushGate: gate);
    final runner = RunCloudSync(local: local, remote: remote,
      accountIdProvider: () async => 'account', platform: 'android',
      deviceName: 'test', appVersion: 'test');
    final first = runner();
    final second = runner();
    expect(identical(first, second), isTrue);
    gate.complete();
    await expectLater(first, throwsStateError);
    await expectLater(second, throwsStateError);
    expect(remote.pushes, 1);
    await expectLater(runner(), throwsStateError);
    expect(remote.pushes, 2);
    expect(local.applied, 0);
  });

}

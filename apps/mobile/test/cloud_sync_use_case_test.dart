import 'package:edunova/src/features/sync/application/cloud_sync_repository.dart';
import 'package:edunova/src/features/sync/application/run_cloud_sync.dart';
import 'package:edunova/src/features/sync/domain/cloud_sync.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeLocal implements CloudSyncLocalRepository {
  final String accountId;
  FakeLocal(this.accountId);

  CloudSyncState state = const CloudSyncState(
    deviceId: 'dev-12345678',
    serverCursor: 0,
    ackedCursor: 0,
    retainedFloor: 0,
    registered: false,
  );
  final mutations = <CloudMutation>[];
  final applied = <CloudRecord>[];
  final conflicts = <SyncConflictView>[];
  bool canonicalResetPrepared = false;

  @override
  Future<CloudSyncState> ensureState(String id) async {
    expect(id, accountId);
    return state;
  }

  @override
  Future<List<CloudMutation>> pendingMutations(String id, {int limit = 100}) async {
    expect(id, accountId);
    return mutations.take(limit).toList();
  }

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

  Future<void> markMutationApplied(String id, String mutationId, CloudRecord? record) async {
    expect(id, accountId);
    mutations.removeWhere((m) => m.id == mutationId);
    if (record != null) applied.add(record);
  }

  @override
  Future<void> markMutationFailed(String id, String mutationId, String error) async {
    expect(id, accountId);
  }

  @override
  Future<void> storeConflict(String id, CloudMutation m, CloudRecord c, String reason) async {
    expect(id, accountId);
    conflicts.add(SyncConflictView(id: 'c1', entityType: m.entityType, entityId: m.entityId, reason: reason, createdAt: DateTime.now()));
  }

  @override
  Future<void> applyRemoteRecord(String id, CloudRecord r) async {
    expect(id, accountId);
    applied.add(r);
  }

  @override
  Future<void> updateCursor(String id, int cursor, {int? retainedFloor, DateTime? syncedAt, DateTime? bootstrappedAt, String? lastError}) async {
    expect(id, accountId);
    state = CloudSyncState(
      deviceId: state.deviceId,
      accountId: id,
      serverCursor: cursor,
      ackedCursor: state.ackedCursor,
      retainedFloor: retainedFloor ?? state.retainedFloor,
      registered: state.registered,
      lastSyncAt: syncedAt ?? state.lastSyncAt,
      lastBootstrapAt: bootstrappedAt ?? state.lastBootstrapAt,
      lastError: lastError,
    );
  }

  @override
  Future<void> markRegistered(String id) async {
    expect(id, accountId);
    state = CloudSyncState(
      deviceId: state.deviceId,
      accountId: id,
      serverCursor: state.serverCursor,
      ackedCursor: state.ackedCursor,
      retainedFloor: state.retainedFloor,
      registered: true,
      lastSyncAt: state.lastSyncAt,
      lastBootstrapAt: state.lastBootstrapAt,
      lastError: state.lastError,
    );
  }

  @override
  Future<void> markAcknowledged(String id, int cursor) async {
    expect(id, accountId);
    state = CloudSyncState(
      deviceId: state.deviceId,
      accountId: id,
      serverCursor: state.serverCursor,
      ackedCursor: cursor,
      retainedFloor: state.retainedFloor,
      registered: state.registered,
      lastSyncAt: state.lastSyncAt,
      lastBootstrapAt: state.lastBootstrapAt,
      lastError: state.lastError,
    );
  }

  @override
  Future<void> applyCanonicalPage(String id, List<CloudRecord> records, int cursor,
      {required int retainedFloor, bool reset = false, DateTime? bootstrappedAt}) async {
    if (reset) await prepareCanonicalReset(id);
    for (final record in records) { await applyRemoteRecord(id, record); }
    await updateCursor(id, cursor, retainedFloor: retainedFloor, bootstrappedAt: bootstrappedAt);
  }

  @override
  Future<void> prepareCanonicalReset(String id) async {
    expect(id, accountId);
    canonicalResetPrepared = true;
  }

  @override
  Future<void> resolveConflict(String id, String conflictId, {required bool keepLocal}) async {
    expect(id, accountId);
  }

  @override
  Stream<CloudSyncState?> watchState(String id) => Stream.value(state);

  @override
  Stream<List<SyncConflictView>> watchOpenConflicts(String id) => Stream.value(conflicts);
}

class FakeRemote implements CloudSyncRemoteGateway {
  bool registered = false;
  int? acknowledged;
  List<PushOutcome> outcomes = [];
  PullPage snapshot = const PullPage(changes: [], nextCursor: 0, hasMore: false);
  PullPage? nextPull;

  @override
  Future<void> registerDevice({required String deviceId, required String name, required String platform, required String appVersion}) async => registered = true;

  @override
  Future<int> acknowledge({required String deviceId, required int cursor}) async {
    acknowledged = cursor;
    return cursor;
  }

  @override
  Future<List<SyncDeviceView>> listDevices() async => const [];

  @override
  Future<void> revokeDevice(String deviceId) async {}

  @override
  Future<List<PushOutcome>> push({required String deviceId, required List<CloudMutation> mutations}) async => outcomes;

  @override
  Future<PullPage> bootstrap({required String deviceId}) async => snapshot;

  @override
  Future<PullPage> pull({required String deviceId, required int cursor, int limit = 200}) async =>
      nextPull ?? PullPage(changes: const [], nextCursor: cursor, hasMore: false);
}

class _FailingAckRemote extends FakeRemote {
  @override
  Future<int> acknowledge({required String deviceId, required int cursor}) async {
    throw StateError('acknowledge_failed');
  }
}

void main() {
  test('failed acknowledgement preserves a committed bootstrap cursor', () async {
    final local = FakeLocal('acc-1');
    final remote = _FailingAckRemote();
    remote.snapshot = const PullPage(changes: [], nextCursor: 12,
        hasMore: false, retainedFloor: 0);
    final sync = RunCloudSync(local: local, remote: remote,
        accountIdProvider: () async => 'acc-1', platform: 'android',
        deviceName: 'test', appVersion: '0.54.8');
    await expectLater(sync(), throwsStateError);
    expect(local.state.serverCursor, 12,
        reason: 'failure diagnostics must not rewind the committed bootstrap');
    expect(local.state.lastError, contains('acknowledge_failed'));
  });

  test('registers, pushes, bootstraps and acknowledges new device per account', () async {
    const accountId = 'acc-1';
    final local = FakeLocal(accountId);
    final remote = FakeRemote();
    final now = DateTime.utc(2026, 9, 21);
    local.mutations.add(CloudMutation(
      id: 'm1', entityType: 'academic_profile', entityId: 'p1', operation: 'upsert',
      payload: const {'faculty': 'Médecine', 'program': 'Médecine humaine', 'level': 'BAC1', 'semester': 'S1'},
      clientModifiedAt: now,
    ));
    final canonical = CloudRecord(
      entityType: 'academic_profile', entityId: 'p1', version: 1,
      payload: const {'faculty': 'Médecine', 'program': 'Médecine humaine', 'level': 'BAC1', 'semester': 'S1'},
      deleted: false, updatedAt: now, serverSeq: 1,
    );
    remote.outcomes = [PushOutcome(mutationId: 'm1', disposition: 'applied', record: canonical)];
    remote.snapshot = PullPage(changes: [canonical], nextCursor: 1, hasMore: false, retainedFloor: 0);

    final result = await RunCloudSync(
      local: local, remote: remote, accountIdProvider: () async => accountId,
      platform: 'android', deviceName: 'test', appVersion: '0.8.1',
    )();

    expect(remote.registered, isTrue);
    expect(result.pushed, 1);
    expect(result.pulled, 1);
    expect(result.cursor, 1);
    expect(remote.acknowledged, 1);
    expect(local.state.ackedCursor, 1);
  });

  test('reset_required rebuilds canonical state without touching local-only documents', () async {
    const accountId = 'acc-2';
    final local = FakeLocal(accountId)
      ..state = const CloudSyncState(
        deviceId: 'dev-stale', accountId: accountId, serverCursor: 4, ackedCursor: 4,
        retainedFloor: 0, registered: true,
      );
    final remote = FakeRemote();
    final now = DateTime.utc(2026, 9, 21);
    final canonical = CloudRecord(
      entityType: 'calendar_event', entityId: 'evt-1', version: 3,
      payload: const {'title': 'Chimie', 'kind': 'interrogation', 'startsAt': '2026-10-01T08:00:00Z'},
      deleted: false, updatedAt: now, serverSeq: 90,
    );
    remote.nextPull = const PullPage(changes: [], nextCursor: 90, hasMore: false, retainedFloor: 40, resetRequired: true);
    remote.snapshot = PullPage(changes: [canonical], nextCursor: 90, hasMore: false, retainedFloor: 40);

    final result = await RunCloudSync(
      local: local, remote: remote, accountIdProvider: () async => accountId,
      platform: 'android', deviceName: 'test', appVersion: '0.8.1',
    )();

    expect(local.canonicalResetPrepared, isTrue);
    expect(result.cursor, 90);
    expect(local.applied, contains(canonical));
    expect(remote.acknowledged, 90);
  });

test('reset_required preserves offline state when canonical snapshot is invalid', () async {
  const accountId = 'acc-reset-invalid';
  final local = FakeLocal(accountId)..state = const CloudSyncState(
    deviceId: 'dev-reset', accountId: accountId, serverCursor: 15,
    ackedCursor: 15, retainedFloor: 0, registered: true);
  final remote = FakeRemote();
  remote.nextPull = const PullPage(
    changes: [], nextCursor: 20, hasMore: false,
    retainedFloor: 16, resetRequired: true);
  remote.snapshot = PullPage(changes: [CloudRecord(
    entityType: 'calendar_event', entityId: 'invalid', version: 0,
    payload: const {}, deleted: false, updatedAt: DateTime.utc(2026),
    serverSeq: 20,
  )], nextCursor: 20, hasMore: false, retainedFloor: 16);
  final sync = RunCloudSync(local: local, remote: remote,
    accountIdProvider: () async => accountId, platform: 'android',
    deviceName: 'test', appVersion: '0.54.4');
  await expectLater(sync(), throwsA(isA<StateError>()));
  expect(local.canonicalResetPrepared, isFalse);
  expect(local.applied, isEmpty);
  expect(local.state.serverCursor, 15);
  expect(local.state.ackedCursor, 15);
});

test('rejects out-of-order delta before writing any record', () async {
  const accountId = 'acc-unordered';
  final local = FakeLocal(accountId)..state = const CloudSyncState(
    deviceId: 'dev-unordered', accountId: accountId, serverCursor: 5,
    ackedCursor: 5, retainedFloor: 0, registered: true);
  final now = DateTime.utc(2026);
  final remote = FakeRemote()..nextPull = PullPage(changes: [
    CloudRecord(entityType: 'calendar_event', entityId: 'newer', version: 2,
      payload: const {}, deleted: false, updatedAt: now, serverSeq: 9),
    CloudRecord(entityType: 'calendar_event', entityId: 'older', version: 1,
      payload: const {}, deleted: false, updatedAt: now, serverSeq: 8),
  ], nextCursor: 9, hasMore: false);
  final sync = RunCloudSync(local: local, remote: remote,
    accountIdProvider: () async => accountId, platform: 'android',
    deviceName: 'test', appVersion: '0.54.4');
  await expectLater(sync(), throwsA(isA<StateError>()));
  expect(local.applied, isEmpty);
  expect(local.state.serverCursor, 5);
});

test('rejects malformed bootstrap before applying any snapshot record', () async {
  final local = FakeLocal('acc-bootstrap');
  final remote = FakeRemote();
  remote.snapshot = PullPage(changes: [
    CloudRecord(entityType: 'calendar_event', entityId: 'e1', version: 1,
      payload: const {}, deleted: false, updatedAt: DateTime.utc(2026), serverSeq: 12),
  ], nextCursor: 10, hasMore: false);
  final sync = RunCloudSync(local: local, remote: remote,
    accountIdProvider: () async => 'acc-bootstrap', platform: 'android',
    deviceName: 'test', appVersion: '0.54.3');
  await expectLater(sync(), throwsA(isA<StateError>()));
  expect(local.applied, isEmpty);
  expect(local.state.serverCursor, 0);
});

test('rejects malformed delta before applying any record', () async {
  final local = FakeLocal('acc-delta')..state = const CloudSyncState(
    deviceId: 'dev-delta', accountId: 'acc-delta', serverCursor: 5,
    ackedCursor: 5, retainedFloor: 0, registered: true);
  final remote = FakeRemote();
  remote.nextPull = PullPage(changes: [
    CloudRecord(entityType: 'calendar_event', entityId: 'e1', version: 1,
      payload: const {}, deleted: false, updatedAt: DateTime.utc(2026), serverSeq: 4),
  ], nextCursor: 6, hasMore: false);
  final sync = RunCloudSync(local: local, remote: remote,
    accountIdProvider: () async => 'acc-delta', platform: 'android',
    deviceName: 'test', appVersion: '0.54.3');
  await expectLater(sync(), throwsA(isA<StateError>()));
  expect(local.applied, isEmpty);
  expect(local.state.serverCursor, 5);
});

}

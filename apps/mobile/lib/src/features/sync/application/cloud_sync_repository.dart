import '../domain/cloud_sync.dart';

abstract interface class CloudSyncLocalRepository {
  Future<CloudSyncState> ensureState(String accountId);
  Future<List<CloudMutation>> pendingMutations(String accountId, {int limit = 100});
  /// Commit every validated push outcome atomically, or leave the entire outbox unchanged.
  Future<void> applyPushOutcomes(String accountId, List<CloudMutation> mutations, List<PushOutcome> outcomes);
  Future<void> markMutationApplied(String accountId, String mutationId, CloudRecord? record);
  Future<void> markMutationFailed(String accountId, String mutationId, String error);
  Future<void> storeConflict(String accountId, CloudMutation mutation, CloudRecord canonical, String reason);
  Future<void> applyRemoteRecord(String accountId, CloudRecord record);
  Future<void> updateCursor(String accountId, int cursor, {int? retainedFloor, DateTime? syncedAt, DateTime? bootstrappedAt, String? lastError});
  /// Record a failed run without changing the durable synchronization cursor.
  /// A failed acknowledgement must never rewind a previously committed page.
  Future<void> recordSyncError(String accountId, String error) async {
    final current = await ensureState(accountId);
    await updateCursor(accountId, current.serverCursor, lastError: error);
  }
  Future<void> markRegistered(String accountId);
  Future<void> markAcknowledged(String accountId, int cursor);
  Future<void> prepareCanonicalReset(String accountId);
  /// Apply a complete validated server page and its checkpoint as one local unit.
  /// Implementations backed by a database must use a single transaction.
  Future<void> applyCanonicalPage(String accountId, List<CloudRecord> records, int cursor,
      {required int retainedFloor, bool reset = false, DateTime? bootstrappedAt});
  Future<void> resolveConflict(String accountId, String conflictId, {required bool keepLocal});
  Stream<CloudSyncState?> watchState(String accountId);
  Stream<List<SyncConflictView>> watchOpenConflicts(String accountId);
  Stream<SyncDiagnostics> watchDiagnostics(String accountId);
}

abstract interface class CloudSyncRemoteGateway {
  Future<void> registerDevice({required String deviceId, required String name, required String platform, required String appVersion});
  Future<int> acknowledge({required String deviceId, required int cursor});
  Future<List<SyncDeviceView>> listDevices();
  Future<void> revokeDevice(String deviceId);
  Future<List<PushOutcome>> push({required String deviceId, required List<CloudMutation> mutations});
  Future<PullPage> pull({required String deviceId, required int cursor, int limit = 200});
  Future<PullPage> bootstrap({required String deviceId});
}

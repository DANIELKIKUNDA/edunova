class CloudSyncState {
  const CloudSyncState({
    required this.deviceId,
    required this.serverCursor,
    required this.ackedCursor,
    required this.retainedFloor,
    required this.registered,
    this.accountId,
    this.lastSyncAt,
    this.lastBootstrapAt,
    this.lastError,
  });

  final String deviceId;
  final String? accountId;
  final int serverCursor;
  final int ackedCursor;
  final int retainedFloor;
  final bool registered;
  final DateTime? lastSyncAt;
  final DateTime? lastBootstrapAt;
  final String? lastError;
}

class CloudMutation {
  const CloudMutation({
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.operation,
    required this.payload,
    required this.clientModifiedAt,
    this.baseVersion,
    this.retryCount = 0,
  });
  final String id;
  final String entityType;
  final String entityId;
  final String operation;
  final Map<String, Object?> payload;
  final int? baseVersion;
  final DateTime clientModifiedAt;
  final int retryCount;
}

class CloudRecord {
  const CloudRecord({
    required this.entityType,
    required this.entityId,
    required this.version,
    required this.payload,
    required this.deleted,
    required this.updatedAt,
    required this.serverSeq,
  });
  final String entityType;
  final String entityId;
  final int version;
  final Map<String, Object?> payload;
  final bool deleted;
  final DateTime updatedAt;
  final int serverSeq;
}

class PushOutcome {
  const PushOutcome({required this.mutationId, required this.disposition, this.reason, this.record, this.canonical});
  final String mutationId;
  final String disposition;
  final String? reason;
  final CloudRecord? record;
  final CloudRecord? canonical;
}

class PullPage {
  const PullPage({required this.changes, required this.nextCursor, required this.hasMore, this.retainedFloor = 0, this.resetRequired = false});
  final List<CloudRecord> changes;
  final int nextCursor;
  final bool hasMore;
  final int retainedFloor;
  final bool resetRequired;
}

class SyncDeviceView {
  const SyncDeviceView({required this.deviceId, required this.name, required this.platform, required this.appVersion, required this.ackedCursor, required this.active, required this.createdAt, required this.lastSeenAt, this.lastSyncAt});
  final String deviceId, name, platform, appVersion;
  final int ackedCursor;
  final bool active;
  final DateTime createdAt, lastSeenAt;
  final DateTime? lastSyncAt;
}

class SyncConflictView {
  const SyncConflictView({required this.id, required this.entityType, required this.entityId, required this.reason, required this.createdAt});
  final String id;
  final String entityType;
  final String entityId;
  final String reason;
  final DateTime createdAt;
}

class SyncRunResult {
  const SyncRunResult({required this.pushed, required this.pulled, required this.conflicts, required this.cursor});
  final int pushed;
  final int pulled;
  final int conflicts;
  final int cursor;
}

class SyncDiagnostics {
  const SyncDiagnostics({required this.pending,required this.deadLetters,required this.openConflicts,required this.oldestPendingAt});
  final int pending;
  final int deadLetters;
  final int openConflicts;
  final DateTime? oldestPendingAt;

  bool get healthy => deadLetters == 0 && openConflicts == 0;
}

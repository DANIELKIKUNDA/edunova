import 'dart:convert';
import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';
import '../../../core/database/app_database.dart';

class CloudMutationWriter {
  const CloudMutationWriter({required this.db, required this.accountIdProvider});
  final AppDatabase db;
  final Future<String?> Function() accountIdProvider;
  static const _uuid = Uuid();

  Future<int?> _baseVersion(String? accountId, String entityType, String entityId) async {
    if (accountId == null) return null;
    final row = await (db.select(db.localAccountSyncEntityVersions)
          ..where((t) => t.accountId.equals(accountId) & t.entityType.equals(entityType) & t.entityId.equals(entityId)))
        .getSingleOrNull();
    return row?.version;
  }

  Future<void> upsert(String entityType, String entityId, Map<String, Object?> payload, DateTime modifiedAt) async {
    final accountId = await accountIdProvider();
    if (accountId == null || accountId.isEmpty) return; // local-only until the user authenticates
    final baseVersion = await _baseVersion(accountId, entityType, entityId);
    final existing = await (db.select(db.localCloudMutations)
          ..where((t) => t.accountId.equals(accountId) & t.entityType.equals(entityType) & t.entityId.equals(entityId) & t.operation.equals('upsert') & t.status.equals('pending'))
          ..orderBy([(t) => OrderingTerm.desc(t.createdAt)])
          ..limit(1))
        .getSingleOrNull();
    final now = DateTime.now().toUtc();
    if (existing != null) {
      await (db.update(db.localCloudMutations)..where((t) => t.id.equals(existing.id))).write(
        LocalCloudMutationsCompanion(
          payloadJson: Value(jsonEncode(payload)), clientModifiedAt: Value(modifiedAt.toUtc()),
          baseVersion: Value(baseVersion ?? existing.baseVersion), retryCount: const Value(0), status: const Value('pending'),
          nextAttemptAt: const Value(null), lastError: const Value(null), createdAt: Value(now),
        ),
      );
      return;
    }
    await db.into(db.localCloudMutations).insert(
      LocalCloudMutationsCompanion.insert(
        id: _uuid.v4(), accountId: Value(accountId), entityType: entityType, entityId: entityId,
        payloadJson: Value(jsonEncode(payload)), baseVersion: Value(baseVersion),
        clientModifiedAt: modifiedAt.toUtc(), createdAt: now,
      ),
    );
  }

  Future<void> delete(String entityType, String entityId, DateTime modifiedAt) async {
    final accountId = await accountIdProvider();
    if (accountId == null || accountId.isEmpty) return;
    final baseVersion = await _baseVersion(accountId, entityType, entityId);
    final pending = await (db.select(db.localCloudMutations)
          ..where((t) => t.accountId.equals(accountId) & t.entityType.equals(entityType) & t.entityId.equals(entityId) & t.status.equals('pending'))
          ..orderBy([(t) => OrderingTerm.desc(t.createdAt)])
          ..limit(1))
        .getSingleOrNull();

    if (pending != null && pending.baseVersion == null) {
      await (db.delete(db.localCloudMutations)..where((t) => t.id.equals(pending.id))).go();
      return;
    }
    final now = DateTime.now().toUtc();
    if (pending != null) {
      await (db.update(db.localCloudMutations)..where((t) => t.id.equals(pending.id))).write(
        LocalCloudMutationsCompanion(
          operation: const Value('delete'), payloadJson: const Value('{}'), baseVersion: Value(baseVersion ?? pending.baseVersion),
          clientModifiedAt: Value(modifiedAt.toUtc()), retryCount: const Value(0), status: const Value('pending'),
          nextAttemptAt: const Value(null), lastError: const Value(null), createdAt: Value(now),
        ),
      );
      return;
    }
    await db.into(db.localCloudMutations).insert(
      LocalCloudMutationsCompanion.insert(
        id: _uuid.v4(), accountId: Value(accountId), entityType: entityType, entityId: entityId,
        operation: const Value('delete'), baseVersion: Value(baseVersion), clientModifiedAt: modifiedAt.toUtc(), createdAt: now,
      ),
    );
  }
}

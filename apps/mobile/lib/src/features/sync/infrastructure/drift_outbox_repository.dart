import 'package:drift/drift.dart';

import '../../../core/database/app_database.dart';
import '../../../core/security/local_account_access.dart';
import '../application/outbox_repository.dart';
import '../domain/outbox_event.dart';

class DriftOutboxRepository implements OutboxRepository {
  DriftOutboxRepository(this._db, {LocalAccountAccess? access}) : _access = access ?? LocalAccountAccess();
  final LocalAccountAccess _access;
  final AppDatabase _db;

  @override
  Future<void> enqueue(OutboxEvent event) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    await _db.transaction(() async {
      await _access.assertUnchanged(revision, owned: true);
      await _db.into(_db.localOutboxItems).insertOnConflictUpdate(
      LocalOutboxItemsCompanion.insert(
        id: event.id,
        aggregateType: event.aggregateType,
        aggregateId: event.aggregateId,
        eventType: event.eventType,
        payloadJson: event.payloadJson,
        occurredAt: event.occurredAt,
        retryCount: Value(event.retryCount),
        status: Value(event.status.name),
      ),
      );
      await _access.assertUnchanged(revision, owned: true);
    });
  }

  @override
  Future<List<OutboxEvent>> pending({int limit = 50}) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    final rows = await (_db.select(_db.localOutboxItems)
          ..where((t) => t.status.equals(OutboxStatus.pending.name))
          ..orderBy([(t) => OrderingTerm.asc(t.occurredAt)])
          ..limit(limit))
        .get();
    await _access.assertUnchanged(revision, owned: true);
    return rows.map(_map).toList(growable: false);
  }

  @override
  Future<void> markSent(String id) => _setStatus(id, OutboxStatus.sent);

  @override
  Future<void> markFailed(String id) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    final row = await (_db.select(_db.localOutboxItems)..where((t) => t.id.equals(id))).getSingleOrNull();
    if (row == null) return;
    await _db.transaction(() async {
      await _access.assertUnchanged(revision, owned: true);
      await (_db.update(_db.localOutboxItems)..where((t) => t.id.equals(id))).write(
      LocalOutboxItemsCompanion(
        status: Value(OutboxStatus.failed.name),
        retryCount: Value(row.retryCount + 1),
      ),
      );
      await _access.assertUnchanged(revision, owned: true);
    });
  }

  Future<void> _setStatus(String id, OutboxStatus status) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    await _db.transaction(() async {
      await _access.assertUnchanged(revision, owned: true);
      await (_db.update(_db.localOutboxItems)..where((t) => t.id.equals(id))).write(
        LocalOutboxItemsCompanion(status: Value(status.name)),
      );
      await _access.assertUnchanged(revision, owned: true);
    });
  }

  OutboxEvent _map(LocalOutboxItem row) => OutboxEvent(
        id: row.id,
        aggregateType: row.aggregateType,
        aggregateId: row.aggregateId,
        eventType: row.eventType,
        payloadJson: row.payloadJson,
        occurredAt: row.occurredAt,
        retryCount: row.retryCount,
        status: OutboxStatus.values.byName(row.status),
      );
}

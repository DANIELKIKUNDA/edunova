import 'package:drift/drift.dart';

import '../../../core/database/app_database.dart';
import '../../../core/security/local_account_access.dart';
import '../application/commerce_repository.dart';
import '../domain/commerce.dart';

class DriftCommerceRepository implements CommerceRepository {
  DriftCommerceRepository(this.db, {LocalAccountAccess? access}) : _access = access ?? LocalAccountAccess();
  final LocalAccountAccess _access;
  final AppDatabase db;

  @override
  Stream<EntitlementSnapshot?> watchEntitlement() => _access.protect((db.select(db.localEntitlementSnapshots)..where((t) => t.id.equals('current'))).watchSingleOrNull().map((r) => r == null ? null : EntitlementSnapshot(
    premium: r.premium,
    premiumUntil: r.premiumUntil,
    aiCreditsRemaining: r.aiCreditsRemaining,
    issuedAt: r.issuedAt,
    offlineValidUntil: r.offlineValidUntil,
    revision: r.revision,
  )), owned: true);

  @override
  Future<void> saveEntitlement(EntitlementSnapshot s) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    await db.transaction(() async {
      await _access.assertUnchanged(revision, owned: true);
      await db.into(db.localEntitlementSnapshots).insertOnConflictUpdate(LocalEntitlementSnapshotsCompanion.insert(
        premium: Value(s.premium), premiumUntil: Value(s.premiumUntil),
        aiCreditsRemaining: Value(s.aiCreditsRemaining), issuedAt: s.issuedAt,
        offlineValidUntil: s.offlineValidUntil, revision: s.revision,
      ));
      await _access.assertUnchanged(revision, owned: true);
    });
  }

  @override
  Stream<List<PaymentIntentView>> watchPayments() => _access.protect((db.select(db.localPaymentIntents)..orderBy([(t) => OrderingTerm.desc(t.createdAt)])).watch().map((rows) => rows.map((r) => PaymentIntentView(
    id: r.id,
    planCode: r.planCode,
    amountCdf: r.amountCdf,
    provider: r.provider,
    providerReference: r.providerReference,
    phoneNumber: r.phoneNumber,
    state: r.state,
    actionType: r.actionType,
    actionValue: r.actionValue,
    userMessage: r.userMessage,
    expiresAt: r.expiresAt,
  )).toList()), owned: true);

  @override
  Future<void> savePayment(PaymentIntentView p) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    await db.transaction(() async {
      await _access.assertUnchanged(revision, owned: true);
      await db.into(db.localPaymentIntents).insertOnConflictUpdate(LocalPaymentIntentsCompanion.insert(
        id: p.id, planCode: p.planCode, amountCdf: p.amountCdf,
        provider: p.provider, providerReference: Value(p.providerReference),
        phoneNumber: p.phoneNumber, state: p.state,
        actionType: Value(p.actionType), actionValue: Value(p.actionValue),
        userMessage: Value(p.userMessage), createdAt: DateTime.now().toUtc(),
        updatedAt: DateTime.now().toUtc(), expiresAt: p.expiresAt,
      ));
      await _access.assertUnchanged(revision, owned: true);
    });
  }

  @override
  Stream<List<ReceiptView>> watchReceipts() => _access.protect((db.select(db.localReceipts)..orderBy([(t) => OrderingTerm.desc(t.issuedAt)])).watch().map((rows) => rows.map((r) => ReceiptView(id: r.id, paymentId: r.paymentId, amountCdf: r.amountCdf, issuedAt: r.issuedAt, description: r.description)).toList()), owned: true);

  @override
  Future<void> replaceReceipts(List<ReceiptView> items) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    await db.transaction(() async {
      await _access.assertUnchanged(revision, owned: true);
      await db.delete(db.localReceipts).go();
      for (final r in items) {
        await db.into(db.localReceipts).insert(LocalReceiptsCompanion.insert(id: r.id, paymentId: r.paymentId, amountCdf: r.amountCdf, issuedAt: r.issuedAt, description: r.description));
      }
      await _access.assertUnchanged(revision, owned: true);
    });
  }
}

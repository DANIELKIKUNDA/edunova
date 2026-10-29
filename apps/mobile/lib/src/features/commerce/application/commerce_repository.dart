import '../domain/commerce.dart';
import '../domain/combined_access.dart';

abstract class CommerceRepository {
  Stream<EntitlementSnapshot?> watchEntitlement();
  Stream<List<PaymentIntentView>> watchPayments();
  Stream<List<ReceiptView>> watchReceipts();
  Future<void> saveEntitlement(EntitlementSnapshot snapshot);
  Future<void> savePayment(PaymentIntentView payment);
  Future<void> replaceReceipts(List<ReceiptView> receipts);
}

abstract class CommerceRemoteGateway {
  Future<CombinedAccessView> getCombinedAccess({String? institutionId});
  Future<List<PremiumPlan>> loadPlans();
  Future<List<PaymentProviderOption>> loadProviders();
  Future<PaymentIntentView> createCheckout({required String planCode, required String phoneNumber, required String provider});
  Future<PaymentIntentView> getPayment(String id);
  Future<EntitlementSnapshot> getEntitlement();
  Future<List<ReceiptView>> getReceipts();
}

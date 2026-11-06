import 'package:dio/dio.dart';
import 'package:uuid/uuid.dart';

import '../../../core/network/api_client.dart';
import '../../identity/application/identity_repository.dart';
import '../application/commerce_repository.dart';
import '../domain/commerce.dart';
import '../domain/combined_access.dart';

class ApiCommerceGateway implements CommerceRemoteGateway {
  ApiCommerceGateway({required ApiClient api, required IdentityRepository identity}) : _api = api, _identity = identity;
  final ApiClient _api;
  final IdentityRepository _identity;
  final _uuid = const Uuid();

  Future<Options> _authOptions({Map<String, dynamic>? headers}) async {
    var session = await _identity.currentSession();
    if (session == null) throw StateError('authentication_required');
    if (session.accessExpired) session = await _identity.refresh();
    return Options(headers: {'Authorization': 'Bearer ${session.accessToken}', ...?headers});
  }

  @override
  Future<List<PaymentProviderOption>> loadProviders() async {
    final r = await _api.dio.get('/v1/commerce/providers');
    return (r.data as List).map((e) { final m = Map<String, dynamic>.from(e); return PaymentProviderOption(code: m['code'], label: m['label'], environment: m['environment']); }).toList();
  }

  @override
  Future<List<PremiumPlan>> loadPlans() async {
    final r = await _api.dio.get('/v1/commerce/plans');
    return (r.data as List).map((e) { final m = Map<String, dynamic>.from(e); return PremiumPlan(
      code: m['code'], name: m['name'], priceCdf: m['price_cdf'], durationDays: m['duration_days'], includedAiCredits: m['included_ai_credits'], maxPersonalDocuments: m['max_personal_documents'], offlineEnabled: m['offline_enabled'],
    ); }).toList();
  }

  @override
  Future<PaymentIntentView> createCheckout({required String planCode, required String phoneNumber, required String provider}) async {
    final r = await _api.dio.post('/v1/commerce/checkout', data: {'plan_code': planCode, 'phone_number': phoneNumber, 'provider': provider}, options: await _authOptions(headers: {'Idempotency-Key': _uuid.v4()}));
    final m = Map<String, dynamic>.from(r.data);
    return PaymentIntentView(id: m['payment_id'], planCode: planCode, amountCdf: m['amount_cdf'], provider: m['provider'], providerReference: m['provider_reference'], phoneNumber: phoneNumber, state: m['state'], actionType: m['action_type'], actionValue: m['action_value'], userMessage: m['user_message'], expiresAt: DateTime.parse(m['expires_at']).toUtc());
  }

  @override
  Future<PaymentIntentView> getPayment(String id) async {
    final r = await _api.dio.get('/v1/commerce/payments/$id', options: await _authOptions());
    final m = Map<String, dynamic>.from(r.data);
    return PaymentIntentView(id: m['id'], planCode: 'premium-30d', amountCdf: m['amount_cdf'], provider: m['provider'], providerReference: m['provider_reference'], phoneNumber: '', state: m['state'], expiresAt: DateTime.now().toUtc().add(const Duration(minutes: 15)));
  }

  @override
  Future<EntitlementSnapshot> getEntitlement() async {
    final r = await _api.dio.get('/v1/commerce/entitlement', options: await _authOptions());
    final m = Map<String, dynamic>.from(r.data);
    return EntitlementSnapshot(
      premium: m['premium'], premiumUntil: m['premium_until'] == null ? null : DateTime.parse(m['premium_until']).toUtc(), aiCreditsRemaining: m['ai_credits_remaining'], issuedAt: DateTime.parse(m['issued_at']).toUtc(), offlineValidUntil: DateTime.parse(m['offline_valid_until']).toUtc(), revision: m['revision'],
    );
  }

  @override
  Future<CombinedAccessView> getCombinedAccess({String? institutionId}) async {
    final query = institutionId == null || institutionId.trim().isEmpty
        ? null
        : <String, dynamic>{'institution_id': institutionId.trim()};
    final response = await _api.dio.get(
      '/v1/commerce/combined-access',
      queryParameters: query,
      options: await _authOptions(),
    );
    return CombinedAccessView.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  @override
  Future<List<ReceiptView>> getReceipts() async {
    final r = await _api.dio.get('/v1/commerce/receipts', options: await _authOptions());
    return (r.data as List).map((e) { final m = Map<String, dynamic>.from(e); return ReceiptView(id: m['id'], paymentId: m['payment_id'], amountCdf: m['amount_cdf'], issuedAt: DateTime.parse(m['issued_at']).toUtc(), description: m['description']); }).toList();
  }
}

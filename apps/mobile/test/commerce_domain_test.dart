import 'package:edunova/src/features/commerce/domain/commerce.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('offline premium requires both lease and subscription to be valid', () {
    final now = DateTime.utc(2026, 9, 20, 12);
    final active = EntitlementSnapshot(premium: true, premiumUntil: now.add(const Duration(days: 20)), aiCreditsRemaining: 10, issuedAt: now, offlineValidUntil: now.add(const Duration(hours: 72)), revision: 'r1');
    expect(active.isPremiumOffline(now.add(const Duration(hours: 48))), isTrue);
    expect(active.isPremiumOffline(now.add(const Duration(hours: 73))), isFalse);
  });

  test('payment terminal states are explicit', () {
    final p = PaymentIntentView(id: 'p', planCode: 'premium-30d', amountCdf: 3000, provider: 'x', state: 'succeeded', phoneNumber: '+243', expiresAt: DateTime.now());
    expect(p.terminal, isTrue);
    expect(p.succeeded, isTrue);
  });
}

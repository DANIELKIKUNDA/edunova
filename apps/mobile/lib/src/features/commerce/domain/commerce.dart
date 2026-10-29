class PremiumPlan {
  const PremiumPlan({
    required this.code,
    required this.name,
    required this.priceCdf,
    required this.durationDays,
    required this.includedAiCredits,
    required this.maxPersonalDocuments,
    required this.offlineEnabled,
  });

  final String code;
  final String name;
  final int priceCdf;
  final int durationDays;
  final int includedAiCredits;
  final int maxPersonalDocuments;
  final bool offlineEnabled;
}

class EntitlementSnapshot {
  const EntitlementSnapshot({
    required this.premium,
    required this.premiumUntil,
    required this.aiCreditsRemaining,
    required this.issuedAt,
    required this.offlineValidUntil,
    required this.revision,
  });

  final bool premium;
  final DateTime? premiumUntil;
  final int aiCreditsRemaining;
  final DateTime issuedAt;
  final DateTime offlineValidUntil;
  final String revision;

  bool isPremiumOffline(DateTime now) => premium && offlineValidUntil.isAfter(now.toUtc()) && (premiumUntil?.isAfter(now.toUtc()) ?? false);
}

class PaymentIntentView {
  const PaymentIntentView({
    required this.id,
    required this.planCode,
    required this.amountCdf,
    required this.provider,
    required this.state,
    required this.phoneNumber,
    required this.expiresAt,
    this.providerReference,
    this.actionType,
    this.actionValue,
    this.userMessage,
  });

  final String id;
  final String planCode;
  final int amountCdf;
  final String provider;
  final String state;
  final String phoneNumber;
  final DateTime expiresAt;
  final String? providerReference;
  final String? actionType;
  final String? actionValue;
  final String? userMessage;

  bool get terminal => const {'succeeded', 'failed', 'expired', 'canceled', 'reversed'}.contains(state);
  bool get succeeded => state == 'succeeded';
}

class ReceiptView {
  const ReceiptView({required this.id, required this.paymentId, required this.amountCdf, required this.issuedAt, required this.description});
  final String id;
  final String paymentId;
  final int amountCdf;
  final DateTime issuedAt;
  final String description;
}

class PaymentProviderOption {
  const PaymentProviderOption({required this.code, required this.label, required this.environment});
  final String code;
  final String label;
  final String environment;
}

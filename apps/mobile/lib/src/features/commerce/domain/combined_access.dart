/// Presentation-only view of independently verified personal and Campus rights.
/// Server-side authorization remains authoritative for Campus resources.
class CombinedAccessView {
  const CombinedAccessView({
    required this.personalPremium,
    required this.campusAccess,
    this.campusInstitutionId,
    this.personalPremiumUntil,
    this.campusAccessUntil,
  });

  final bool personalPremium;
  final bool campusAccess;
  final String? campusInstitutionId;
  final DateTime? personalPremiumUntil;
  final DateTime? campusAccessUntil;

  String get personalTier => personalPremium ? 'premium' : 'free';

  factory CombinedAccessView.fromJson(Map<String, dynamic> json) {
    return CombinedAccessView(
      personalPremium: json['personal_premium'] == true,
      personalPremiumUntil: json['personal_premium'] == true && json['personal_premium_until'] is String
          ? DateTime.tryParse(json['personal_premium_until'] as String)?.toUtc() : null,
      campusAccessUntil: json['campus_access'] == true && json['campus_access_until'] is String
          ? DateTime.tryParse(json['campus_access_until'] as String)?.toUtc() : null,
      campusAccess: json['campus_access'] == true,
      campusInstitutionId: json['campus_access'] == true
          ? json['campus_institution_id'] as String?
          : null,
    );
  }
}

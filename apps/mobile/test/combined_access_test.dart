import 'package:flutter_test/flutter_test.dart';
import 'package:edunova/src/features/commerce/domain/combined_access.dart';

void main() {
  test('Campus does not grant personal Premium', () {
    final value = CombinedAccessView.fromJson({
      'personal_premium': false,
      'campus_access': true,
      'campus_institution_id': 'uni-a',
    });
    expect(value.personalTier, 'free');
    expect(value.campusAccess, true);
  });

  test('Suspended Campus does not remove personal Premium', () {
    final value = CombinedAccessView.fromJson({
      'personal_premium': true,
      'campus_access': false,
      'campus_institution_id': 'uni-a',
    });
    expect(value.personalTier, 'premium');
    expect(value.campusInstitutionId, isNull);
  });
}

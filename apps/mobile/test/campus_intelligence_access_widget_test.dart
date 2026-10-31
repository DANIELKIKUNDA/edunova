import 'package:edunova/src/core/di/providers.dart';
import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus/presentation/campus_page.dart';
import 'package:edunova/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart';
import 'package:edunova/src/features/campus_intelligence/presentation/institution_intelligence_page.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class NoSession implements IdentityRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class FakeCampusGateway extends CampusIntelligenceGateway {
  FakeCampusGateway({required this.membershipRole, this.membershipState = 'active', this.institutionId = 'i1'})
      : super(api: ApiClient(), identity: NoSession());
  final String membershipRole, membershipState, institutionId;
  int teacherCalls = 0, executiveCalls = 0;

  @override
  Future<List<Map<String, dynamic>>> institutions() async => [{
    'institution': {'id': institutionId, 'name': 'Université Test', 'state': 'active'},
    'membership': {'role': membershipRole, 'state': membershipState, 'unit_id': 'faculty-1'},
  }];

  @override
  Future<List<Map<String, dynamic>>> offerings(String iid) async => [
    {'id': 'off-1', 'label': 'Cours de physique'}
  ];

  @override
  Future<List<Map<String, dynamic>>> periods(String iid) async => [
    {'id': 'p1', 'name': 'Semestre 1', 'active': true},
    {'id': 'p2', 'name': 'Semestre 2', 'active': true},
  ];

  @override
  Future<Map<String, dynamic>> teachingDashboard(String iid, String offeringId) async {
    teacherCalls++;
    return {'summary': {'objective_count': 0, 'high_priority_count': 0, 'unassessed_count': 0},
      'objectives': [], 'priority_actions': [], 'recurrent_errors': []};
  }

  @override
  Future<Map<String, dynamic>> gradebookReconciliation(String iid, String offeringId) async =>
    {'status': 'no_published_gradebook', 'candidate_count': null};

  @override
  Future<Map<String, dynamic>> objectiveReport(String iid, String offeringId) async =>
    {'objectives': [], 'limitations': []};

  @override
  Future<List<Map<String, dynamic>>> snapshotHistory(String iid,
      {String? periodId, String? unitId}) async => [];

  @override
  Future<Map<String, dynamic>> executiveReadout(String iid, {String? periodId, String? unitId}) async {
    executiveCalls++;
    return {'quality': {'status': 'insufficient_population'},
      'indicators': [{'metric': 'results.pass_rate', 'status': 'suppressed', 'observed_percent': null}],
      'priorities': []};
  }
}

void main() {
  Widget wrap(Widget child, FakeCampusGateway fake) => ProviderScope(
    overrides: [campusIntelligenceGatewayProvider.overrideWithValue(fake),
      campusVerifiedAlumniProvider.overrideWith((ref) async => [])],
    child: MaterialApp(home: child));

  testWidgets('membre étudiant : aucun accès aux analyses', (tester) async {
    final fake = FakeCampusGateway(membershipRole: 'student');
    await tester.pumpWidget(wrap(const CampusPage(), fake));
    await tester.pumpAndSettle();
    final tile = tester.widget<ListTile>(find.ancestor(
      of: find.text('Université Test'), matching: find.byType(ListTile)).first);
    expect(tile.onTap, isNull);
  });

  testWidgets('invitation non acceptée : accès interdit', (tester) async {
    final fake = FakeCampusGateway(membershipRole: 'teacher', membershipState: 'invited');
    await tester.pumpWidget(wrap(const CampusPage(), fake));
    await tester.pumpAndSettle();
    final tile = tester.widget<ListTile>(find.ancestor(
      of: find.text('Université Test'), matching: find.byType(ListTile)).first);
    expect(tile.onTap, isNull);
  });

  testWidgets('URL directe vers autre université : aucune requête analytique', (tester) async {
    final fake = FakeCampusGateway(membershipRole: 'rector', institutionId: 'allowed');
    await tester.pumpWidget(wrap(
      const InstitutionIntelligencePage(institutionId: 'other-tenant'), fake));
    await tester.pumpAndSettle();
    expect(fake.teacherCalls, 0);
    expect(fake.executiveCalls, 0);
    expect(find.textContaining('Accès institutionnel indisponible'), findsOneWidget);
  });

  testWidgets('auditeur actif : accès aux indicateurs, pas à la gestion pédagogique', (tester) async {
    final fake = FakeCampusGateway(membershipRole: 'auditor');
    await tester.pumpWidget(wrap(
      const InstitutionIntelligencePage(institutionId: 'i1'), fake));
    await tester.pumpAndSettle();
    expect(fake.teacherCalls, 0);
    expect(fake.executiveCalls, 1);
    expect(find.textContaining('Intelligence institutionnelle'), findsOneWidget);
    expect(find.textContaining('Intelligence pédagogique'), findsNothing);
  });

  testWidgets('direction : masque les pourcentages supprimés', (tester) async {
    final fake = FakeCampusGateway(membershipRole: 'rector');
    await tester.pumpWidget(wrap(
      const InstitutionIntelligencePage(institutionId: 'i1'), fake));
    await tester.pumpAndSettle();
    expect(fake.executiveCalls, 1);
    await tester.tap(find.text('Intelligence institutionnelle').last);
    await tester.pumpAndSettle();
    expect(find.text('Masqué / non disponible'), findsOneWidget);
    expect(find.text('0.0 %'), findsNothing);
  });
}

import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart';
import 'package:edunova/src/features/campus_intelligence/presentation/institutional_archive_panel.dart';
import 'package:edunova/src/features/campus_intelligence/presentation/pedagogical_governance_panel.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _NotUsedIdentity implements IdentityRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _FakeGateway extends CampusIntelligenceGateway {
  _FakeGateway(): super(api: ApiClient(), identity: _NotUsedIdentity());
  int writes = 0;
  int captures = 0;
  String? lastInstitution, lastOffering;

  @override
  Future<Map<String, dynamic>> objectiveReport(String iid, String offeringId) async {
    lastInstitution = iid; lastOffering = offeringId;
    return {'objectives': [
      {'objective_id': 'PHY_01', 'title': 'Cinématique',
        'evidence_integrity': 'legacy_unverified',
        'mapping_provenance': 'contains_retrospective_mapping'},
    ], 'limitations': ['La provenance historique est incertaine.']};
  }

  @override
  Future<Map<String, dynamic>> registerObjective(String iid, String offeringId,
      {required String objectiveId, required String title}) async {
    lastInstitution = iid; lastOffering = offeringId; writes++;
    return {'objective_id': objectiveId};
  }

  @override
  Future<List<Map<String, dynamic>>> snapshotHistory(String iid,
      {String? periodId, String? unitId}) async => [
    {'privacy_status': 'historical_temporal_suppressed',
      'payload': {'secret_student_grade': 'FAKE_PRIVATE_GRADE_19_20'}},
  ];

  @override
  Future<Map<String, dynamic>> captureSnapshot(String iid,
      {String? periodId, String? unitId}) async {
    captures++;
    return {'id': 'snap1'};
  }

  @override
  Future<Map<String, dynamic>> archiveComparison(String iid,
      {String? periodId, String? unitId}) async => {
    'available': false, 'reason': 'unverified_or_privacy_suppressed_snapshots',
    'items': [],
  };
}

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(
  body: SingleChildScrollView(child: child)));

void main() {
  testWidgets('ph14: formulaire lié au vrai cours sans altération des notes', (tester) async {
    final fake = _FakeGateway();
    await tester.pumpWidget(_wrap(PedagogicalGovernancePanel(
      gateway: fake, institutionId: 'uni_ok', offeringId: 'off_ok')));
    await tester.pumpAndSettle();
    expect(fake.lastInstitution, 'uni_ok');
    expect(fake.lastOffering, 'off_ok');
    expect(find.text('Cinématique'), findsOneWidget);
    expect(find.textContaining('provenance historique'), findsOneWidget);
    await tester.enterText(find.byType(TextField).at(0), 'OBJ_02');
    await tester.enterText(find.byType(TextField).at(1), 'Dynamique');
    await tester.ensureVisible(find.text('Enregistrer l’objectif'));
    await tester.tap(find.text('Enregistrer l’objectif'));
    await tester.pumpAndSettle();
    expect(fake.writes, 1);
    expect(find.textContaining('enregistré et contrôlé'), findsOneWidget);
  });

  testWidgets('ph15: un auditeur ne reçoit aucun contrôle de capture', (tester) async {
    final fake = _FakeGateway();
    await tester.pumpWidget(_wrap(InstitutionalArchivePanel(
      gateway: fake, institutionId: 'uni_ok', allowCapture: false)));
    await tester.pumpAndSettle();
    expect(find.text('Créer une capture'), findsNothing);
    expect(fake.captures, 0);
  });

  testWidgets('ph15: archive bloquée ne divulgue jamais son payload', (tester) async {
    final fake = _FakeGateway();
    await tester.pumpWidget(_wrap(InstitutionalArchivePanel(
      gateway: fake, institutionId: 'uni_ok', unitId: 'fac_ok')));
    await tester.pumpAndSettle();
    expect(find.textContaining('historical_temporal_suppressed'), findsOneWidget);
    expect(find.textContaining('FAKE_PRIVATE_GRADE'), findsNothing);
    await tester.ensureVisible(find.text('Créer une capture'));
    await tester.tap(find.text('Créer une capture'));
    await tester.pumpAndSettle();
    expect(find.text('Confirmer la capture'), findsOneWidget);
    expect(fake.captures, 0);
    await tester.tap(find.text('Annuler'));
    await tester.pumpAndSettle();
    expect(fake.captures, 0);
    await tester.ensureVisible(find.text('Comparer les archives'));
    await tester.tap(find.text('Comparer les archives'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Comparaison historique indisponible'), findsOneWidget);
    expect(find.textContaining('FAKE_PRIVATE_GRADE'), findsNothing);
  });
}

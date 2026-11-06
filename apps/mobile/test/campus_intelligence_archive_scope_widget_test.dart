import 'dart:async';

import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart';
import 'package:edunova/src/features/campus_intelligence/presentation/institutional_archive_panel.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _UnusedIdentity implements IdentityRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _ScopedGateway extends CampusIntelligenceGateway {
  _ScopedGateway() : super(api: ApiClient(), identity: _UnusedIdentity());
  final oldCsv = Completer<String>();
  int captured = 0;

  @override
  Future<List<Map<String, dynamic>>> snapshotHistory(String iid,
      {String? periodId, String? unitId}) async => [];

  @override
  Future<String> csvPreview(String iid, {String? periodId, String? unitId}) async =>
      periodId == 'old-period' ? oldCsv.future : 'metric,value\nNEW_PERIOD_ONLY,1\n';

  @override
  Future<Map<String, dynamic>> captureSnapshot(String iid,
      {String? periodId, String? unitId}) async {
    captured++;
    return {'id': 'capture'};
  }
}

void main() {
  Widget wrap(_ScopedGateway gateway, {required String period, bool allowCapture = true}) =>
      MaterialApp(home: Scaffold(body: SingleChildScrollView(
        child: InstitutionalArchivePanel(
          key: const ValueKey('reuse-archive-state'), gateway: gateway,
          institutionId: 'uni1', periodId: period, allowCapture: allowCapture))));

  testWidgets('une réponse CSV périmée ne réapparaît pas après changement de période', (tester) async {
    final gateway = _ScopedGateway();
    await tester.pumpWidget(wrap(gateway, period: 'old-period'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Aperçu CSV sécurisé'));
    await tester.pump();
    await tester.pumpWidget(wrap(gateway, period: 'new-period'));
    await tester.pumpAndSettle();
    gateway.oldCsv.complete('metric,value\nOLD_PRIVATE_ARCHIVE,19\n');
    await tester.pumpAndSettle();
    expect(find.textContaining('OLD_PRIVATE_ARCHIVE'), findsNothing);
    await tester.tap(find.text('Aperçu CSV sécurisé'));
    await tester.pumpAndSettle();
    expect(find.textContaining('NEW_PERIOD_ONLY'), findsOneWidget);
    await tester.pumpWidget(wrap(gateway, period: 'old-period'));
    await tester.pump();
    expect(find.textContaining('NEW_PERIOD_ONLY'), findsNothing);
  });

  testWidgets('passage en arrière-plan efface le CSV et invalide les requêtes', (tester) async {
    final gateway = _ScopedGateway();
    await tester.pumpWidget(wrap(gateway, period: 'new-period'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Aperçu CSV sécurisé'));
    await tester.pumpAndSettle();
    expect(find.textContaining('NEW_PERIOD_ONLY'), findsOneWidget);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.inactive);
    await tester.pump();
    expect(find.textContaining('NEW_PERIOD_ONLY'), findsNothing);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pumpAndSettle();
    expect(find.textContaining('NEW_PERIOD_ONLY'), findsNothing);
  });

  testWidgets('révocation de capture pendant la confirmation empêche le POST', (tester) async {
    final gateway = _ScopedGateway();
    await tester.pumpWidget(wrap(gateway, period: 'new-period'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Créer une capture'));
    await tester.pumpAndSettle();
    expect(find.text('Confirmer la capture'), findsOneWidget);
    await tester.pumpWidget(wrap(gateway, period: 'new-period', allowCapture: false));
    await tester.pump();
    await tester.tap(find.text('Confirmer la capture'));
    await tester.pumpAndSettle();
    expect(gateway.captured, 0);
    expect(find.text('Créer une capture'), findsNothing);
  });
}

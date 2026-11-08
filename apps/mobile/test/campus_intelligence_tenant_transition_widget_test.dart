import 'dart:async';

import 'package:dio/dio.dart';

import 'package:edunova/src/core/di/providers.dart';
import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart';
import 'package:edunova/src/features/campus_intelligence/presentation/institution_intelligence_page.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _UnusedIdentity implements IdentityRepository {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _TransitionGateway extends CampusIntelligenceGateway {
  _TransitionGateway() : super(api: ApiClient(), identity: _UnusedIdentity());
  final oldTenantResponse = Completer<Map<String, dynamic>>();
  bool awaitingFirstA = true;

  @override
  Future<List<Map<String, dynamic>>> institutions() async => [
    for (final iid in ['uni-A', 'uni-B']) {
      'institution': {'id': iid, 'name': 'Université $iid', 'state': 'active'},
      'membership': {'role': 'teacher', 'state': 'active'},
    }
  ];

  @override
  Future<List<Map<String, dynamic>>> offerings(String iid) async => [
    {'id': 'off-A', 'label': 'Cours A'},
    {'id': 'off-B', 'label': 'Cours B'},
  ];

  @override
  Future<Map<String, dynamic>> teachingDashboard(String iid, String offeringId) async {
    if (iid == 'uni-A' && offeringId == 'off-A' && awaitingFirstA) {
      awaitingFirstA = false;
      return oldTenantResponse.future;
    }
    return {
      'summary': {'objective_count': 1, 'high_priority_count': 0, 'unassessed_count': 0},
      'objectives': [{
        'objective_title': iid == 'uni-B' ? 'PUBLIC_B_NEW' : 'AUTHORIZED_A_NEW',
        'coverage': 0.5,
      }],
      'priority_actions': [], 'recurrent_errors': [], 'assessment_timeline': [],
    };
  }

  @override
  Future<Map<String, dynamic>> gradebookReconciliation(String iid, String offeringId) async => {};

  @override
  Future<Map<String, dynamic>> objectiveReport(String iid, String offeringId) async => {
    'objectives': [], 'limitations': [],
  };
}


class _AmbiguousOfferingsGateway extends _TransitionGateway {
  @override
  Future<List<Map<String, dynamic>>> offerings(String iid) async => [
    {'id': 'duplicate', 'label': 'Cours 1'},
    {'id': 'duplicate', 'label': 'Cours 2'},
  ];
}

class _RevokedGateway extends _TransitionGateway {
  int dashboardRequests = 0;
  @override
  Future<Map<String, dynamic>> teachingDashboard(String iid, String offeringId) async {
    dashboardRequests++;
    if (dashboardRequests > 1) {
      final request = RequestOptions(path: '/v1/pedagogical-intelligence');
      throw DioException(requestOptions: request,
        response: Response<dynamic>(requestOptions: request, statusCode: 403));
    }
    return {
      'summary': {'objective_count': 1},
      'objectives': [{'objective_title': 'SENSITIVE_BEFORE_REVOKE', 'coverage': 0.5}],
    };
  }
}

void main() {
  testWidgets('référence de cours ambiguë : aucune analyse exécutée', (tester) async {
    final fake = _AmbiguousOfferingsGateway();
    await tester.pumpWidget(ProviderScope(
      overrides: [campusIntelligenceGatewayProvider.overrideWithValue(fake)],
      child: const MaterialApp(home: InstitutionIntelligencePage(institutionId: 'uni-A')),
    ));
    await tester.pumpAndSettle();
    expect(find.textContaining('Accès institutionnel indisponible'), findsOneWidget);
    expect(find.text('OLD_OUTDATED_RESULT'), findsNothing);
  });

  testWidgets('403 après publication : le tableau privé précédent est effacé', (tester) async {
    final fake = _RevokedGateway();
    await tester.pumpWidget(ProviderScope(
      overrides: [campusIntelligenceGatewayProvider.overrideWithValue(fake)],
      child: const MaterialApp(home: InstitutionIntelligencePage(institutionId: 'uni-A')),
    ));
    await tester.pumpAndSettle();
    expect(find.text('SENSITIVE_BEFORE_REVOKE'), findsOneWidget);
    await tester.tap(find.byTooltip('Actualiser et revérifier les droits'));
    await tester.pumpAndSettle();
    expect(find.text('SENSITIVE_BEFORE_REVOKE'), findsNothing);
    expect(find.textContaining('Accès refusé'), findsOneWidget);
  });

  testWidgets('changement de tenant : une réponse tardive de A ne divulgue rien dans B', (tester) async {
    final fake = _TransitionGateway();
    Widget page(String id) => ProviderScope(
      overrides: [campusIntelligenceGatewayProvider.overrideWithValue(fake)],
      child: MaterialApp(home: InstitutionIntelligencePage(
        key: const ValueKey('same-state-reused-by-router'), institutionId: id)),
    );

    await tester.pumpWidget(page('uni-A'));
    await tester.pump();
    await tester.pumpWidget(page('uni-B'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Université uni-B'), findsOneWidget);
    expect(find.text('PUBLIC_B_NEW'), findsOneWidget);
    fake.oldTenantResponse.complete({
      'summary': {}, 'objectives': [
        {'objective_title': 'CONFIDENTIAL_UNI_A', 'coverage': 0.9}
      ]
    });
    await tester.pumpAndSettle();
    expect(find.text('CONFIDENTIAL_UNI_A'), findsNothing);
    expect(find.text('PUBLIC_B_NEW'), findsOneWidget);
  });

  testWidgets('A-B-A : une ancienne requête du même cours ne remplace pas la récente', (tester) async {
    final fake = _TransitionGateway();
    await tester.pumpWidget(ProviderScope(
      overrides: [campusIntelligenceGatewayProvider.overrideWithValue(fake)],
      child: const MaterialApp(home: InstitutionIntelligencePage(institutionId: 'uni-A')),
    ));
    // A is still awaiting a response; do not pumpAndSettle while its loading
    // animation is alive. Only advance the dropdown animation explicitly.
    await tester.pump();

    Future<void> chooseCourse(String label) async {
      await tester.tap(find.byType(DropdownButtonFormField<String>).first);
      await tester.pump(const Duration(milliseconds: 350));
      await tester.tap(find.text(label).last);
      await tester.pump(const Duration(milliseconds: 350));
    }

    await chooseCourse('Cours B');
    expect(find.text('AUTHORIZED_A_NEW'), findsOneWidget);
    await chooseCourse('Cours A');
    expect(find.text('AUTHORIZED_A_NEW'), findsOneWidget);
    fake.oldTenantResponse.complete({
      'summary': {}, 'objectives': [
        {'objective_title': 'OLD_OUTDATED_RESULT', 'coverage': 0.1}
      ]
    });
    await tester.pumpAndSettle();
    expect(find.text('OLD_OUTDATED_RESULT'), findsNothing);
    expect(find.text('AUTHORIZED_A_NEW'), findsOneWidget);
  });
}

import 'package:dio/dio.dart';
import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:edunova/src/features/identity/domain/auth_session.dart';
import 'package:flutter_test/flutter_test.dart';

class StubIdentity implements IdentityRepository {
  StubIdentity(this.session);
  AuthSession? session;
  @override
  Future<AuthSession?> currentSession() async => session;
  @override
  Future<AuthSession> refresh() async => session!;
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

AuthSession validSession() => AuthSession(
  accountId: 'account1', displayName: 'Responsable', accessToken: 'test-token',
  refreshToken: 'refresh', expiresAt: DateTime.now().toUtc().add(const Duration(hours: 1)),
);

void main() {
  group('Confidentialité: aucune valeur masquée déduite côté Flutter', () {
    test('valeurs nulles, invalides et non libérées restent indisponibles', () {
      expect(releasedPercent(null, 'available'), 'Masqué / non disponible');
      expect(releasedPercent(0, 'suppressed'), 'Masqué / non disponible');
      expect(releasedPercent(82, 'temporal_disclosure_suppressed'), 'Masqué / non disponible');
      expect(releasedPercent(100.1, 'available'), 'Masqué / non disponible');
      expect(releasedPercent(0, 'available'), '0.0 %');
      expect(releasedPercent(82.35, 'available'), '82.3 %');
      expect(releasedDelta(null, 'comparable'), 'Comparaison indisponible');
      expect(releasedDelta(1.5, 'privacy_suppressed'), 'Comparaison indisponible');
      expect(releasedDelta(-1.5, 'comparable'), '-1.5 points');
    });
  });

  group('API institutionnelle authentifiée', () {
    late Dio dio;
    late CampusIntelligenceGateway gateway;
    late List<RequestOptions> requests;
    setUp(() {
      dio = Dio(BaseOptions(baseUrl: 'https://edunova.example'));
      requests = [];
      dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        dynamic body;
        if (options.path.endsWith('/me/institutions')) {
          body = <dynamic>[];
        } else if (options.path.endsWith('/me/offerings') || options.path.endsWith('/periods')) {
          body = <dynamic>[];
        } else {
          body = <String, dynamic>{'contract_version': 1, 'status': 'available'};
        }
        handler.resolve(Response<dynamic>(requestOptions: options, data: body, statusCode: 200));
      }));
      gateway = CampusIntelligenceGateway(api: ApiClient(dio: dio),
        identity: StubIdentity(validSession()));
    });

    test('selection, scope, jeton et absence de mutation', () async {
      expect(await gateway.institutions(), isEmpty);
      await gateway.offerings('inst-1');
      await gateway.periods('inst-1');
      await gateway.teachingDashboard('inst-1', 'off-1');
      await gateway.gradebookReconciliation('inst-1', 'off-1');
      await gateway.executiveReadout('inst-1', periodId: 'p-1', unitId: 'fac-1');
      await gateway.periodComparison('inst-1', previousPeriodId: 'p-1',
        currentPeriodId: 'p-2', unitId: 'fac-1');
      expect(requests, hasLength(7));
      expect(requests.every((r) => r.method == 'GET'), isTrue);
      expect(requests.every((r) => r.headers['Authorization'] == 'Bearer test-token'), isTrue);
      expect(requests.every((r) => r.extra['campus_intelligence_no_cache'] == true), isTrue);
      expect(requests[3].path, contains('/pedagogical-intelligence/institutions/inst-1/offerings/off-1/dashboard'));
      expect(requests[5].queryParameters['academic_unit_id'], 'fac-1');
      expect(requests[6].queryParameters['previous_period_id'], 'p-1');
      expect(requests[6].queryParameters['current_period_id'], 'p-2');
    });

    test('tenant path injection et comparaison absurde refusés avant le réseau', () async {
      await expectLater(gateway.teachingDashboard('inst/../foreign', 'off'),
        throwsA(isA<ArgumentError>()));
      await expectLater(gateway.periodComparison('inst-1', previousPeriodId: 'p-1',
        currentPeriodId: 'p-1'), throwsA(isA<ArgumentError>()));
      expect(requests, isEmpty);
    });

    test('aucune requête sans session authentifiée', () async {
      final blocked = CampusIntelligenceGateway(api: ApiClient(dio: dio),
        identity: StubIdentity(null));
      await expectLater(blocked.institutions(), throwsA(isA<StateError>()));
      expect(requests, isEmpty);
    });
  });
}

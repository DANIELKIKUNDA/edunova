import 'package:dio/dio.dart';
import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus_services/infrastructure/campus_services_gateway.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:edunova/src/features/identity/domain/auth_session.dart';
import 'package:flutter_test/flutter_test.dart';

class AlertsSessionStub implements IdentityRepository {
  final session = AuthSession(accountId: 'student', displayName: 'Étudiant',
    accessToken: 'token-alert', refreshToken: 'refresh-alert',
    expiresAt: DateTime.now().toUtc().add(const Duration(hours: 1)));
  @override
  Future<AuthSession?> currentSession() async => session;
  @override
  Future<AuthSession> refresh() async => session;
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  test('Alertes personnelles : GET scellé au tenant, bearer, no-cache', () async {
    final seen = <RequestOptions>[];
    final dio = Dio(BaseOptions(baseUrl: 'https://example.org'));
    dio.interceptors.add(InterceptorsWrapper(onRequest: (req, handler) {
      seen.add(req);
      handler.resolve(Response<dynamic>(requestOptions: req, statusCode: 200,
        data: <dynamic>[{'id': 'library_due:1', 'kind': 'library_due',
          'title': 'Retour prochain', 'message': 'Livre à restituer',
          'level': 'warning', 'occurs_at': '2026-10-19T08:00:00+00:00'}]));
    }));
    final gateway = CampusServicesGateway(api: ApiClient(dio: dio),
      identity: AlertsSessionStub());
    expect((await gateway.campusAlerts('uni-1')).single['level'], 'warning');
    expect(seen.single.method, 'GET');
    expect(seen.single.path, '/v1/campus-services/institutions/uni-1/alerts');
    expect(seen.single.headers['Authorization'], 'Bearer token-alert');
    expect(seen.single.headers['Cache-Control'], 'no-store');
    await expectLater(() => gateway.campusAlerts('../uni-2'), throwsArgumentError);
  });

  test('Réponses malformées et doublons ne doivent pas être affichés', () async {
    final dio = Dio(BaseOptions(baseUrl: 'https://example.org'));
    dio.interceptors.add(InterceptorsWrapper(onRequest: (req, handler) {
      handler.resolve(Response<dynamic>(requestOptions: req, statusCode: 200,
        data: <dynamic>[
          {'id': '1', 'title': 'A', 'message': 'B', 'level': 'info'},
          {'id': '1', 'title': 'A', 'message': 'B', 'level': 'info'},
        ]));
    }));
    final gateway = CampusServicesGateway(api: ApiClient(dio: dio),
      identity: AlertsSessionStub());
    await expectLater(() => gateway.campusAlerts('uni-a'), throwsFormatException);
  });
}

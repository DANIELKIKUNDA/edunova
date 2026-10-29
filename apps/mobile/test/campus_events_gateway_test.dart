import 'package:dio/dio.dart';
import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus_services/infrastructure/campus_services_gateway.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:edunova/src/features/identity/domain/auth_session.dart';
import 'package:flutter_test/flutter_test.dart';

class EventSessionStub implements IdentityRepository {
  final AuthSession session = AuthSession(
    accountId: 'member-1', displayName: 'Étudiant',
    accessToken: 'events-token', refreshToken: 'refresh-token',
    expiresAt: DateTime.now().toUtc().add(const Duration(hours: 1)),
  );
  @override
  Future<AuthSession?> currentSession() async => session;
  @override
  Future<AuthSession> refresh() async => session;
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  test('Événements : routes scellées au tenant et au bearer; versions conservées', () async {
    final requests = <RequestOptions>[];
    final dio = Dio(BaseOptions(baseUrl: 'https://edunova.example'));
    dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
      requests.add(options);
      handler.resolve(Response<dynamic>(requestOptions: options,
        statusCode: 200, data: options.method == 'GET'
          ? <dynamic>[] : <String, dynamic>{'id': 'ok'}));
    }));
    final gateway = CampusServicesGateway(api: ApiClient(dio: dio),
      identity: EventSessionStub());
    await gateway.events('uni-a');
    await gateway.myEventRegistrations('uni-a');
    await gateway.configureEventCapacity('uni-a', 'cev-1', 2, 45);
    await gateway.registerForEvent('uni-a', 'cev-1');
    await gateway.withdrawFromEvent('uni-a', 'cev-1', 3);
    await gateway.publishCampusEvent('uni-a', title: 'Conférence',
      details: 'Scientifique', location: 'Amphithéâtre',
      startsAt: DateTime.utc(2026, 12, 1, 12),
      endsAt: DateTime.utc(2026, 12, 1, 14));
    expect(requests.map((r) => r.method).toList(),
      ['GET', 'GET', 'PUT', 'POST', 'POST', 'POST']);
    expect(requests.every((r) => r.headers['Authorization'] == 'Bearer events-token'), true);
    expect(requests.every((r) => r.headers['Cache-Control'] == 'no-store'), true);
    expect(requests[2].data, {'expected_version': 2, 'capacity': 45});
    expect(requests[4].data, {'expected_version': 3});
    expect(requests[5].data['kind'], 'event');
    expect(requests.every((r) => r.path.contains('/institutions/uni-a/')), true);
  });

  test('Identifiants de tenants dangereux rejetés sans requête réseau', () async {
    final dio = Dio(BaseOptions(baseUrl: 'https://edunova.example'));
    final gateway = CampusServicesGateway(api: ApiClient(dio: dio),
      identity: EventSessionStub());
    await expectLater(() => gateway.events('../uni-b'), throwsArgumentError);
    await expectLater(() => gateway.registerForEvent('uni-a', '../../priv'), throwsArgumentError);
  });
}

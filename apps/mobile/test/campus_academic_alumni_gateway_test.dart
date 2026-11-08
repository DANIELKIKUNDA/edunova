import 'package:dio/dio.dart';
import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus_services/infrastructure/campus_services_gateway.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:edunova/src/features/identity/domain/auth_session.dart';
import 'package:flutter_test/flutter_test.dart';

class _Identity implements IdentityRepository {
  _Identity(this.session);
  AuthSession? session;
  @override
  Future<AuthSession?> currentSession() async => session;
  @override
  Future<AuthSession> refresh() async => session!;
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  late CampusServicesGateway api;
  late List<RequestOptions> requests;
  late _Identity identity;
  setUp(() {
    requests = [];
    final dio = Dio(BaseOptions(baseUrl: 'https://api.edunova.example'));
    dio.interceptors.add(InterceptorsWrapper(onRequest: (request, handler) {
      requests.add(request);
      dynamic data;
      if (request.method == 'GET') {
        data = request.path.endsWith('/alumni/me') ? null :
          request.path.endsWith('/academic-unassigned')
            ? <String, dynamic>{'calendar_count': 0, 'teaching_count': 0,
                'truncated': false, 'calendar': <dynamic>[], 'teaching': <dynamic>[]}
            : <dynamic>[];
      } else {
        data = <String, dynamic>{'id': 'ok'};
      }
      handler.resolve(Response<dynamic>(requestOptions: request, statusCode: 200, data: data));
    }));
    identity = _Identity(AuthSession(accountId: 'account-1', displayName: 'Ancien étudiant',
      accessToken: 'alumni-access', refreshToken: 'refresh',
      expiresAt: DateTime.now().toUtc().add(const Duration(hours: 1))));
    api = CampusServicesGateway(api: ApiClient(dio: dio), identity: identity);
  });

  test('Affection d’un événement du calendrier, libération CAS, tenant', () async {
    await api.academicAllocations('uni-a');
    await api.teachingAllocations('uni-a');
    await api.assignAcademicRoom('uni-a', 'cev-3', 'res-4');
    await api.assignTeachingRoom('uni-a', 'ses-9', 'res-5');
    await api.releaseAcademicRoom('uni-a', 'ars-3', 2);
    await api.releaseTeachingRoom('uni-a', 'tra-9', 4);
    expect(requests.map((r) => r.method).toList(), ['GET', 'GET', 'POST', 'POST', 'POST', 'POST']);
    expect(requests[2].data, {'calendar_event_id': 'cev-3', 'resource_id': 'res-4'});
    expect(requests[3].data, {'teaching_session_id': 'ses-9', 'resource_id': 'res-5'});
    expect(requests[4].data, {'expected_version': 2});
    expect(requests[5].data, {'expected_version': 4});
    expect(requests[4].path, endsWith('/academic-allocations/ars-3/release'));
    expect(requests[5].path, endsWith('/teaching-allocations/tra-9/release'));
    expect(requests.every((r) => r.path.contains('/institutions/uni-a/')), isTrue);
  });

  test('Réconciliation des séances et découverte Alumni vérifiée, sans cache', () async {
    final pending = await api.academicUnassigned('uni-a');
    expect(pending['calendar_count'], 0);
    await api.alumniMyInstitutions();
    expect(requests[0].path, endsWith('/institutions/uni-a/academic-unassigned'));
    expect(requests[1].path, '/v1/campus-services/alumni/my-institutions');
    expect(requests.every((r) => r.headers['Authorization'] == 'Bearer alumni-access'), isTrue);
    expect(requests.every((r) => r.headers['Cache-Control'] == 'no-store'), isTrue);
    expect(requests.every((r) => r.headers['Pragma'] == 'no-cache'), isTrue);
  });

  test('Alumni : consentement explicite, validation et opportunités gouvernées', () async {
    expect(await api.alumniMe('uni-a'), isNull);
    await api.applyAlumni('uni-a', name: 'Marie', program: 'Santé', year: 2024,
      headline: 'Médecin', visible: false, version: 0);
    await api.alumniDirectory('uni-a');
    await api.alumniPending('uni-a');
    await api.alumniDecide('uni-a', 'alm-1', 1, 'verified', 'registry-2024');
    await api.alumniOpportunities('uni-a');
    await api.alumniPublishOpportunity('uni-a', 'Offre stage', 'Étudiants avancés',
      'https://example.org/postulez');
    await api.alumniWithdrawOpportunity('uni-a', 'alo-1', 1);
    expect(requests.length, 8);
    expect(requests[1].method, 'PUT');
    expect((requests[1].data as Map)['visible'], false);
    expect((requests[1].data as Map)['expected_version'], 0);
    expect((requests[4].data as Map)['reference'], 'registry-2024');
    expect((requests[7].data as Map)['expected_version'], 1);
    expect(requests.every((r) => r.headers['Authorization'] == 'Bearer alumni-access'), isTrue);
    expect(requests.every((r) => r.headers['Cache-Control'] == 'no-store'), isTrue);
  });

  test('Isolation du chemin d’université et absence de session', () async {
    await expectLater(api.alumniDirectory('../uni-b'), throwsA(isA<ArgumentError>()));
    await expectLater(api.assignAcademicRoom('uni-a', '../cev-1', 'res-1'),
      throwsA(isA<ArgumentError>()));
    await expectLater(api.releaseAcademicRoom('uni-a', '../ars', 1),
      throwsA(isA<ArgumentError>()));
    identity.session = null;
    await expectLater(api.alumniMe('uni-a'), throwsA(isA<StateError>()));
    expect(requests, isEmpty);
  });
}

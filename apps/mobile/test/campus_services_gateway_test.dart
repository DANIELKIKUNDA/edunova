import 'package:dio/dio.dart';
import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus_services/infrastructure/campus_services_gateway.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:edunova/src/features/identity/domain/auth_session.dart';
import 'package:flutter_test/flutter_test.dart';

class StubCampusIdentity implements IdentityRepository {
  StubCampusIdentity(this.session);
  AuthSession? session;
  @override
  Future<AuthSession?> currentSession() async => session;
  @override
  Future<AuthSession> refresh() async => session!;
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

AuthSession validCampusSession() => AuthSession(
  accountId: 'student1', displayName: 'Étudiant', accessToken: 'token-16',
  refreshToken: 'refresh', expiresAt: DateTime.now().toUtc().add(const Duration(hours: 1)),
);

void main() {
  late Dio dio;
  late List<RequestOptions> requests;
  late CampusServicesGateway gateway;
  setUp(() {
    dio = Dio(BaseOptions(baseUrl: 'https://edunova.example'));
    requests = [];
    dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
      requests.add(options);
      final dynamic data = options.path.endsWith('/library/policy')
          ? <String, dynamic>{'row_version': 3, 'loan_days': 21,
              'max_open_loans': 3, 'max_renewals': 2, 'renewal_days': 14}
          : options.method == 'GET' ? <dynamic>[] : <String, dynamic>{'id': 'test'};
      handler.resolve(Response<dynamic>(requestOptions: options, data: data, statusCode: 200));
    }));
    gateway = CampusServicesGateway(api: ApiClient(dio: dio),
      identity: StubCampusIdentity(validCampusSession()));
  });

  test('Ressources, réservations et annulation restent liées à une institution', () async {
    await gateway.institutions();
    await gateway.resources('uni-1');
    await gateway.bookings('uni-1');
    await gateway.register('uni-1', kind: 'room', code: 'R1', name: 'Salle',
      location: 'Bloc A', capacity: 30);
    final start = DateTime.utc(2026, 10, 25, 9);
    await gateway.reserve('uni-1', resourceId: 'res-1', purpose: 'TP',
      startsAt: start, endsAt: start.add(const Duration(hours: 2)));
    await gateway.cancel('uni-1', 'bkg-1', 2);
    expect(requests.length, 6);
    expect(requests.map((r) => r.method).toList(),
      ['GET', 'GET', 'GET', 'POST', 'POST', 'POST']);
    expect(requests.every((r) => r.headers['Authorization'] == 'Bearer token-16'), isTrue);
    expect(requests.every((r) => r.extra['campus_services_no_cache'] == true), isTrue);
    expect(requests[4].path, endsWith('/v1/campus-services/institutions/uni-1/bookings'));
    expect((requests[4].data as Map)['starts_at'], start.toIso8601String());
    expect(requests[5].path, endsWith('/bookings/bkg-1/cancel'));
    expect((requests[5].data as Map)['expected_version'], 2);
  });

  test('Identifiants chemin malformés et absence de session sont refusés', () async {
    await expectLater(gateway.resources('../uni-b'), throwsA(isA<ArgumentError>()));
    await expectLater(gateway.cancel('uni-1', 'other/123', 1), throwsA(isA<ArgumentError>()));
    final offline = CampusServicesGateway(api: ApiClient(dio: dio),
      identity: StubCampusIdentity(null));
    await expectLater(offline.resources('uni-1'), throwsA(isA<StateError>()));
    expect(requests, isEmpty);
  });

  test('Bibliothèque physique : prêts, retours et exemplaires authentifiés', () async {
    await gateway.physicalBooks('uni-1');
    await gateway.physicalCopies('uni-1');
    await gateway.physicalLoans('uni-1');
    await gateway.addPhysicalBook('uni-1', title: 'Physique', author: 'Auteur');
    await gateway.addPhysicalCopy('uni-1', bookId: 'libb-1', barcode: 'P-001');
    await gateway.borrowPhysicalCopy('uni-1', 'libc-1');
    await gateway.returnPhysicalLoan('uni-1', 'libl-1', 3);
    expect(requests.map((r) => r.method).toList(),
        ['GET', 'GET', 'GET', 'POST', 'POST', 'POST', 'POST']);
    expect(requests[3].path, endsWith('/library/books'));
    expect(requests[4].path, endsWith('/library/copies'));
    expect(requests[5].path, endsWith('/library/loans'));
    expect(requests[6].path, endsWith('/library/loans/libl-1/return'));
    expect((requests[5].data as Map)['copy_id'], 'libc-1');
    expect((requests[6].data as Map)['expected_version'], 3);
    expect(requests.every((r) => r.extra['campus_services_no_cache'] == true), isTrue);
    expect(requests.every((r) => r.headers['Authorization'] == 'Bearer token-16'), isTrue);
  });

  test('Prolongations : identité issue du token et version anti-rejeu', () async {
    await gateway.renewPhysicalLoan('uni-1', 'libl-23', 4);
    expect(requests, hasLength(1));
    expect(requests.single.method, 'POST');
    expect(requests.single.path, endsWith(
        '/v1/campus-services/institutions/uni-1/library/loans/libl-23/renew'));
    expect(requests.single.data, {'expected_version': 4});
    expect(requests.single.headers['Authorization'], 'Bearer token-16');
    expect(requests.single.extra['campus_services_no_cache'], true);
    await expectLater(gateway.renewPhysicalLoan('uni-1', '../libl-b', 1),
        throwsA(isA<ArgumentError>()));
    expect(requests, hasLength(1));
  });

  test('Politique de bibliothèque : lecture et sauvegarde avec CAS', () async {
    final policy = await gateway.physicalLibraryPolicy('uni-1');
    expect(policy['row_version'], 3);
    await gateway.updatePhysicalLibraryPolicy('uni-1', expectedVersion: 3,
      loanDays: 18, maxOpenLoans: 4, maxRenewals: 1, renewalDays: 10);
    expect(requests, hasLength(2));
    expect(requests[0].method, 'GET');
    expect(requests[1].method, 'PUT');
    expect(requests[1].path, endsWith('/institutions/uni-1/library/policy'));
    expect(requests[1].data, {
      'expected_version': 3, 'loan_days': 18, 'max_open_loans': 4,
      'max_renewals': 1, 'renewal_days': 10,
    });
    expect(requests.every((r) => r.headers['Authorization'] == 'Bearer token-16'), isTrue);
    expect(requests.every((r) => r.extra['campus_services_no_cache'] == true), isTrue);
  });

  test('Politique : interdiction de chemin interuniversitaire invalide', () async {
    await expectLater(gateway.updatePhysicalLibraryPolicy('../autre',
      expectedVersion: 0, loanDays: 21, maxOpenLoans: 3,
      maxRenewals: 2, renewalDays: 14), throwsA(isA<ArgumentError>()));
    await expectLater(gateway.physicalLibraryPolicy('uni/abc'),
        throwsA(isA<ArgumentError>()));
    expect(requests, isEmpty);
  });

  test('Identifiants emprunts malformés et session manquante sont rejetés', () async {
    await expectLater(gateway.borrowPhysicalCopy('../a', 'libc-1'), throwsA(isA<ArgumentError>()));
    await expectLater(gateway.returnPhysicalLoan('uni-1', '../autre', 1),
        throwsA(isA<ArgumentError>()));
    final denied = CampusServicesGateway(api: ApiClient(dio: dio),
      identity: StubCampusIdentity(null));
    await expectLater(denied.physicalLoans('uni-1'), throwsA(isA<StateError>()));
    expect(requests, isEmpty);
  });


  test('Incidents : perte et détérioration versionnées, même université', () async {
    await gateway.reportPhysicalLoanIncident('uni-1', 'libl-9', 4, 'damaged');
    await gateway.reportPhysicalLoanIncident('uni-1', 'libl-8', 1, 'lost');
    expect(requests, hasLength(2));
    expect(requests[0].path, endsWith('/library/loans/libl-9/incident'));
    expect(requests[0].data, {'expected_version': 4, 'condition': 'damaged'});
    expect(requests[1].data, {'expected_version': 1, 'condition': 'lost'});
    expect(requests.every((r) => r.headers['Authorization'] == 'Bearer token-16'), true);
    expect(requests.every((r) => r.extra['campus_services_no_cache'] == true), true);
  });

  test('Incidents : restauration versionnée et entrée falsifiée refusée', () async {
    await gateway.restoreDamagedPhysicalCopy('uni-1', 'libc-5', 2);
    expect(requests.single.path, endsWith('/library/copies/libc-5/restore'));
    expect(requests.single.data, {'expected_version': 2});
    await expectLater(gateway.reportPhysicalLoanIncident('uni-1', 'libl-1',
      1, 'returned'), throwsA(isA<ArgumentError>()));
    await expectLater(gateway.restoreDamagedPhysicalCopy('../other', 'libc-1', 2),
      throwsA(isA<ArgumentError>()));
    expect(requests, hasLength(1));
  });


  test('Maintenance : signalement et transition avec isolation institutionnelle', () async {
    await gateway.maintenanceTickets('uni-1');
    await gateway.reportMaintenance('uni-1', 'res-7',
      'Équipement endommagé pendant le cours.');
    await gateway.transitionMaintenance('uni-1', 'mnt-9', 'start', 1, '');
    await gateway.transitionMaintenance('uni-1', 'mnt-9', 'resolve', 2,
      'Vérification du remplacement effectuée.');
    expect(requests, hasLength(4));
    expect(requests[0].path, endsWith('/institutions/uni-1/maintenance'));
    expect(requests[1].method, 'POST');
    expect(requests[1].data, {
      'resource_id': 'res-7',
      'description': 'Équipement endommagé pendant le cours.',
    });
    expect(requests[2].path, endsWith('/maintenance/mnt-9/start'));
    expect(requests[2].data, {'expected_version': 1, 'note': ''});
    expect(requests[3].path, endsWith('/maintenance/mnt-9/resolve'));
    expect((requests[3].data as Map)['expected_version'], 2);
    expect(requests.every((r) => r.headers['Authorization'] == 'Bearer token-16'), isTrue);
    expect(requests.every((r) => r.extra['campus_services_no_cache'] == true), isTrue);
  });

  test('Maintenance : chemins malformés et action inconnue refusés', () async {
    await expectLater(gateway.maintenanceTickets('../uni-b'), throwsA(isA<ArgumentError>()));
    await expectLater(gateway.reportMaintenance('uni-1', '../resource', 'Défaut avéré'),
      throwsA(isA<ArgumentError>()));
    await expectLater(gateway.transitionMaintenance('uni-1', 'mnt-1',
      'delete', 1, ''), throwsA(isA<ArgumentError>()));
    await expectLater(gateway.transitionMaintenance('uni-1', 'other/id',
      'start', 1, ''), throwsA(isA<ArgumentError>()));
    expect(requests, isEmpty);
  });

}

import 'package:dio/dio.dart';
import 'package:edunova/src/core/network/api_client.dart';
import 'package:edunova/src/features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart';
import 'package:edunova/src/features/identity/application/identity_repository.dart';
import 'package:edunova/src/features/identity/domain/auth_session.dart';
import 'package:flutter_test/flutter_test.dart';

class _SessionStub implements IdentityRepository {
  _SessionStub({this.authenticated = true});
  final bool authenticated;
  @override
  Future<AuthSession?> currentSession() async => authenticated
    ? AuthSession(accountId: 'staff1', displayName: 'Personnel', accessToken: 'secret',
        refreshToken: 'refresh', expiresAt: DateTime.now().toUtc().add(const Duration(hours: 2)))
    : null;
  @override
  Future<AuthSession> refresh() async => (await currentSession())!;
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  late Dio dio;
  late List<RequestOptions> requests;
  late CampusIntelligenceGateway gateway;

  setUp(() {
    requests = [];
    dio = Dio(BaseOptions(baseUrl: 'https://edunova.example'));
    dio.interceptors.add(InterceptorsWrapper(onRequest: (req, handler) {
      requests.add(req);
      if (req.path.endsWith('/objectives/report')) {
        handler.resolve(Response<dynamic>(requestOptions: req, statusCode: 200,
          data: {'objectives': [], 'limitations': []}));
      } else if (req.path.contains('/snapshots') && req.method == 'GET') {
        handler.resolve(Response<dynamic>(requestOptions: req, statusCode: 200,
          data: {'items': [{'privacy_status': 'historical_temporal_suppressed', 'payload': null}]}));
      } else if (req.path.contains('/export.csv')) {
        handler.resolve(Response<dynamic>(requestOptions: req, statusCode: 200,
          headers: Headers.fromMap({'content-type': ['text/csv; charset=utf-8']}),
          data: 'section,metric,value\n'));
      } else {
        handler.resolve(Response<dynamic>(requestOptions: req, statusCode: 200,
          data: {'ok': true, 'available': false}));
      }
    }));
    gateway = CampusIntelligenceGateway(api: ApiClient(dio: dio),
      identity: _SessionStub());
  });

  test('ph14 objectifs: lecture et POST seulement sur métadonnées autorisées', () async {
    await gateway.objectiveReport('uni1', 'off1');
    await gateway.registerObjective('uni1', 'off1', objectiveId: 'OBJ_1', title: 'Cinématique');
    await gateway.mapQuestion('uni1', 'off1', objectiveId: 'OBJ_1', questionId: 'q1');
    await gateway.bindBlueprint('uni1', 'off1', blueprintId: 'b1');
    expect(requests.map((r) => r.method), ['GET', 'POST', 'POST', 'POST']);
    expect(requests[1].data['objective_id'], 'OBJ_1');
    expect(requests[2].data['question_id'], 'q1');
    expect(requests[3].path, contains('/assessment-blueprints'));
    expect(requests.every((r) => r.headers['Authorization'] == 'Bearer secret'), isTrue);
    expect(requests.every((r) => r.headers['Cache-Control'] == 'no-store'), isTrue);
    expect(requests.every((r) => r.extra['campus_intelligence_no_cache'] == true), isTrue);
    expect(requests.every((r) => !r.path.contains('/jury/')), isTrue);
  });

  test('ph15 archives: périmètre faculté, export volatil, historique gouverné', () async {
    final history = await gateway.snapshotHistory('uni1', unitId: 'fac1', periodId: 'sem1');
    expect(history.single['payload'], isNull);
    await gateway.captureSnapshot('uni1', unitId: 'fac1', periodId: 'sem1');
    await gateway.archiveComparison('uni1', unitId: 'fac1', periodId: 'sem1');
    expect(await gateway.csvPreview('uni1', unitId: 'fac1'), contains('metric'));
    expect(requests.map((r) => r.method), ['GET', 'POST', 'GET', 'GET']);
    expect(requests[0].queryParameters['scope_type'], 'academic_unit');
    expect(requests[0].queryParameters['scope_id'], 'fac1');
    expect(requests[1].queryParameters['academic_unit_id'], 'fac1');
    expect(requests[2].queryParameters['scope_id'], 'fac1');
  });

  test('chemins injectés, champs invalides et session absente bloqués', () async {
    expect(() => gateway.mapQuestion('uni1', 'off1',
      objectiveId: '../forbidden', questionId: 'q1'), throwsArgumentError);
    expect(() => gateway.bindBlueprint('uni1', 'off1', blueprintId: 'x/y'),
      throwsArgumentError);
    expect(() => gateway.registerObjective('uni1', 'off1',
      objectiveId: '   ', title: 'Nom'), throwsArgumentError);
    await expectLater(gateway.snapshotHistory('uni/other'), throwsArgumentError);
    final blocked = CampusIntelligenceGateway(api: ApiClient(dio: dio),
      identity: _SessionStub(authenticated: false));
    await expectLater(blocked.captureSnapshot('uni1'), throwsStateError);
    expect(requests, isEmpty);
  });
}

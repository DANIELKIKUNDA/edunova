import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../identity/application/identity_repository.dart';

/// Phase 14–15: queries are always remote, identity-bound and read-only.
/// Restricted aggregates MUST NOT be cached in the offline local database.
class CampusIntelligenceGateway {
  CampusIntelligenceGateway({required ApiClient api, required IdentityRepository identity})
      : _api = api, _identity = identity;
  final ApiClient _api;
  final IdentityRepository _identity;

  static String _id(String id) {
    if (!RegExp(r'^[a-zA-Z0-9_-]{1,128}$').hasMatch(id)) {
      throw ArgumentError.value(id, 'id', 'Identifiant institutionnel invalide');
    }
    return Uri.encodeComponent(id);
  }

  Future<Options> _auth() async {
    var session = await _identity.currentSession();
    if (session == null) throw StateError('authentication_required');
    if (session.accessExpired) session = await _identity.refresh();
    return Options(headers: {'Authorization': 'Bearer ${session.accessToken}',
      'Cache-Control': 'no-store', 'Pragma': 'no-cache'},
      extra: {'campus_intelligence_no_cache': true});
  }

  Future<dynamic> _get(String path, [Map<String, String>? query]) async {
    final response = await _api.dio.get<dynamic>(
      path, queryParameters: query,
      options: await _auth(),
    );
    return response.data;
  }

  Future<List<Map<String, dynamic>>> institutions() async =>
      _maps(await _get('/v1/campus/me/institutions'));

  Future<List<Map<String, dynamic>>> offerings(String iid) async =>
      _maps(await _get('/v1/teaching/institutions/${_id(iid)}/me/offerings'));

  Future<List<Map<String, dynamic>>> periods(String iid) async =>
      _maps(await _get('/v1/campus/institutions/${_id(iid)}/periods'));

  Future<Map<String, dynamic>> teachingDashboard(String iid, String offeringId) async =>
      _map(await _get('/v1/pedagogical-intelligence/institutions/${_id(iid)}/offerings/${_id(offeringId)}/dashboard'));

  Future<Map<String, dynamic>> gradebookReconciliation(String iid, String offeringId) async =>
      _map(await _get('/v1/pedagogical-intelligence/institutions/${_id(iid)}/offerings/${_id(offeringId)}/gradebook-reconciliation'));

  Future<Map<String, dynamic>> executiveReadout(String iid, {String? periodId, String? unitId}) async =>
      _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/intelligence/executive-readout', {
        if (periodId != null) 'academic_period_id': _id(periodId),
        if (unitId != null) 'academic_unit_id': _id(unitId),
      }));

  Future<Map<String, dynamic>> periodComparison(String iid,
      {required String previousPeriodId, required String currentPeriodId, String? unitId}) async {
    if (previousPeriodId == currentPeriodId) throw ArgumentError('distinct_periods_required');
    return _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/intelligence/period-comparison', {
      'previous_period_id': _id(previousPeriodId),
      'current_period_id': _id(currentPeriodId),
      if (unitId != null) 'academic_unit_id': _id(unitId),
    }));
  }

  /// Authenticated mutations are limited to pedagogical *metadata*: no grades.
  Future<Map<String, dynamic>> _post(String path, [Map<String, dynamic>? body,
      Map<String, String>? query]) async {
    final response = await _api.dio.post<dynamic>(
      path, queryParameters: query, data: body, options: await _auth(),
    );
    return _map(response.data);
  }

  static String _requiredText(String text, int max, String field) {
    final value = text.trim();
    if (value.isEmpty || value.length > max || value.contains(RegExp(r'[\x00-\x1f\x7f]'))) {
      throw ArgumentError.value(field, 'field', 'Champ obligatoire ou invalide');
    }
    return value;
  }

  Future<Map<String, dynamic>> objectiveReport(String iid, String offeringId) async =>
    _map(await _get('/v1/pedagogical-intelligence/institutions/${_id(iid)}/offerings/${_id(offeringId)}/objectives/report'));

  Future<Map<String, dynamic>> registerObjective(String iid, String offeringId,
      {required String objectiveId, required String title}) =>
    _post('/v1/pedagogical-intelligence/institutions/${_id(iid)}/offerings/${_id(offeringId)}/objectives', {
      'objective_id': _requiredText(objectiveId, 120, 'objective_id'),
      'title': _requiredText(title, 500, 'title'),
    });

  Future<Map<String, dynamic>> mapQuestion(String iid, String offeringId,
      {required String objectiveId, required String questionId}) =>
    _post('/v1/pedagogical-intelligence/institutions/${_id(iid)}/offerings/${_id(offeringId)}/objectives/${_id(objectiveId)}/questions', {
      'question_id': _id(questionId),
    });

  Future<Map<String, dynamic>> bindBlueprint(String iid, String offeringId,
      {required String blueprintId}) =>
    _post('/v1/pedagogical-intelligence/institutions/${_id(iid)}/offerings/${_id(offeringId)}/assessment-blueprints', {
      'blueprint_id': _id(blueprintId),
    });

  /// Server-governed archives: no cross-tenant wildcard permitted.
  Future<List<Map<String, dynamic>>> snapshotHistory(String iid,
      {String? periodId, String? unitId}) async {
    final response = _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/snapshots', {
      'scope_type': unitId == null ? 'institution' : 'academic_unit',
      if (unitId != null) 'scope_id': _id(unitId),
      if (periodId != null) 'academic_period_id': _id(periodId),
      'limit': '20',
    }));
    return _maps(response['items']);
  }

  Future<Map<String, dynamic>> captureSnapshot(String iid,
      {String? periodId, String? unitId}) =>
    _post('/v1/institutional-analytics/institutions/${_id(iid)}/snapshots', null, {
      if (periodId != null) 'academic_period_id': _id(periodId),
      if (unitId != null) 'academic_unit_id': _id(unitId),
    });

  Future<Map<String, dynamic>> archiveComparison(String iid,
      {String? periodId, String? unitId}) async =>
    _map(await _get('/v1/institutional-analytics/institutions/${_id(iid)}/comparisons', {
      'scope_type': unitId == null ? 'institution' : 'academic_unit',
      if (unitId != null) 'scope_id': _id(unitId),
      if (periodId != null) 'academic_period_id': _id(periodId),
    }));

  /// Bounded in-memory preview; NEVER write restricted aggregates to local storage.
  Future<String> csvPreview(String iid, {String? periodId, String? unitId}) async {
    final query = {
        if (periodId != null) 'academic_period_id': _id(periodId),
        if (unitId != null) 'academic_unit_id': _id(unitId),
      };
    final options = (await _auth()).copyWith(responseType: ResponseType.plain);
    final response = await _api.dio.get<String>(
      '/v1/institutional-analytics/institutions/${_id(iid)}/export.csv',
      queryParameters: query, options: options);
    final body = response.data;
    final contentType = response.headers.value(Headers.contentTypeHeader) ?? '';
    if (body == null || body.length > 262144 ||
        !contentType.toLowerCase().contains('text/csv')) {
      throw const FormatException('Export CSV indisponible ou trop volumineux');
    }
    return body;
  }

  static Map<String, dynamic> _map(dynamic data) {
    if (data is! Map) throw const FormatException('Réponse institutionnelle invalide');
    return Map<String, dynamic>.from(data);
  }

  static List<Map<String, dynamic>> _maps(dynamic data) {
    if (data is! List) throw const FormatException('Liste institutionnelle invalide');
    return data.map(_map).toList(growable: false);
  }
}

/// No client-side inference from hidden data: only explicit released values.
String releasedPercent(dynamic value, String status) {
  if (status != 'available' || value is! num || !value.isFinite ||
      value < 0 || value > 100) return 'Masqué / non disponible';
  return '${value.toStringAsFixed(1)} %';
}

String releasedDelta(dynamic value, String status) {
  if (status != 'comparable' || value is! num || !value.isFinite ||
      value < -100 || value > 100) return 'Comparaison indisponible';
  return '${value >= 0 ? '+' : ''}${value.toStringAsFixed(1)} points';
}

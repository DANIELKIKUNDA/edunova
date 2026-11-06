import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../identity/application/identity_repository.dart';

/// Remote-only institutional resource operations. No offline tenant cache.
class CampusServicesGateway {
  CampusServicesGateway({required ApiClient api, required IdentityRepository identity})
      : _api = api, _identity = identity;

  final ApiClient _api;
  final IdentityRepository _identity;

  static String _id(String id) {
    if (!RegExp(r'^[a-zA-Z0-9_-]{1,128}$').hasMatch(id)) {
      throw ArgumentError.value(id, 'id', 'Identifiant Campus invalide');
    }
    return Uri.encodeComponent(id);
  }

  Future<Options> _options() async {
    var session = await _identity.currentSession();
    if (session == null) throw StateError('authentication_required');
    if (session.accessExpired) session = await _identity.refresh();
    return Options(headers: {
      'Authorization': 'Bearer ${session.accessToken}',
      'Cache-Control': 'no-store',
      'Pragma': 'no-cache',
    }, extra: {'campus_services_no_cache': true});
  }

  String _base(String iid) => '/v1/campus-services/institutions/${_id(iid)}';

  static Map<String, dynamic> _map(dynamic result) {
    if (result is! Map) throw const FormatException('Réponse Campus invalide');
    return Map<String, dynamic>.from(result);
  }

  static List<Map<String, dynamic>> _maps(dynamic result) {
    if (result is! List) throw const FormatException('Liste Campus invalide');
    return result.map(_map).toList(growable: false);
  }

  Future<Map<String, dynamic>> academicUnassigned(String iid) async {
    final result = await _api.dio.get<dynamic>(
      '${_base(iid)}/academic-unassigned', options: await _options());
    return _map(result.data);
  }

  Future<List<Map<String, dynamic>>> alumniMyInstitutions() async {
    final result = await _api.dio.get<dynamic>(
      '/v1/campus-services/alumni/my-institutions', options: await _options());
    return _maps(result.data);
  }

  Future<List<Map<String, dynamic>>> institutions() async {
    final result = await _api.dio.get<dynamic>('/v1/campus/me/institutions',
        options: await _options());
    return _maps(result.data);
  }

  // Alertes personnelles recalculées sur le serveur; aucune mise en cache offline.
  Future<List<Map<String, dynamic>>> campusAlerts(String iid) async {
    final response = await _api.dio.get<dynamic>('${_base(iid)}/alerts',
        options: await _options());
    final rows = _maps(response.data);
    final ids = <String>{};
    for (final row in rows) {
      if (row['id'] is! String || !ids.add(row['id'] as String) ||
          !const {'urgent', 'warning', 'info'}.contains(row['level']) ||
          row['title'] is! String || row['message'] is! String) {
        throw const FormatException('Alerte Campus invalide ou dupliquée');
      }
    }
    return rows;
  }

  // Physical room assignment to canonical teaching_sessions: not a second timetable.
  Future<List<Map<String, dynamic>>> teachingAllocations(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/teaching-allocations',
        options: await _options());
    return _maps(r.data);
  }

  Future<Map<String, dynamic>> assignTeachingRoom(String iid,
      String sessionId, String resourceId) async {
    final r = await _api.dio.post<dynamic>('${_base(iid)}/teaching-allocations',
        data: {'teaching_session_id': _id(sessionId), 'resource_id': _id(resourceId)},
        options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> releaseTeachingRoom(String iid,
      String assignmentId, int version) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/teaching-allocations/${_id(assignmentId)}/release',
        data: {'expected_version': version}, options: await _options());
    return _map(r.data);
  }

  // Academic-room allocations reference canonical campus calendar events.
  Future<List<Map<String, dynamic>>> academicAllocations(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/academic-allocations',
        options: await _options());
    return _maps(r.data);
  }

  Future<Map<String, dynamic>> assignAcademicRoom(String iid,
      String eventId, String resourceId) async {
    final r = await _api.dio.post<dynamic>('${_base(iid)}/academic-allocations',
        data: {'calendar_event_id': _id(eventId), 'resource_id': _id(resourceId)},
        options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> releaseAcademicRoom(String iid,
      String assignmentId, int version) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/academic-allocations/${_id(assignmentId)}/release',
        data: {'expected_version': version}, options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>?> alumniMe(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/alumni/me',
        options: await _options());
    return r.data == null ? null : _map(r.data);
  }

  Future<Map<String, dynamic>> applyAlumni(String iid, {
    required String name, required String program, required int year,
    required String headline, required bool visible, required int version,
  }) async {
    final r = await _api.dio.put<dynamic>('${_base(iid)}/alumni/me',
        data: {'display_name': name, 'program_name': program,
          'graduation_year': year, 'headline': headline, 'visible': visible,
          'expected_version': version}, options: await _options());
    return _map(r.data);
  }

  Future<List<Map<String, dynamic>>> alumniDirectory(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/alumni/directory',
        options: await _options());
    return _maps(r.data);
  }

  Future<List<Map<String, dynamic>>> alumniPending(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/alumni/pending',
        options: await _options());
    return _maps(r.data);
  }

  Future<Map<String, dynamic>> alumniDecide(String iid, String profileId,
      int version, String decision, String reference) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/alumni/${_id(profileId)}/decide',
        data: {'expected_version': version, 'decision': decision,
          'reference': reference}, options: await _options());
    return _map(r.data);
  }

  Future<List<Map<String, dynamic>>> alumniOpportunities(String iid) async {
    final r = await _api.dio.get<dynamic>(
        '${_base(iid)}/alumni/opportunities', options: await _options());
    return _maps(r.data);
  }

  Future<Map<String, dynamic>> alumniPublishOpportunity(String iid,
      String title, String description, String url) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/alumni/opportunities', data: {'title': title,
          'description': description, 'application_url': url}, options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> alumniWithdrawOpportunity(String iid,
      String opportunityId, int version) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/alumni/opportunities/${_id(opportunityId)}/withdraw',
        data: {'expected_version': version}, options: await _options());
    return _map(r.data);
  }

  Future<List<Map<String, dynamic>>> resources(String iid) async {
    final result = await _api.dio.get<dynamic>('${_base(iid)}/resources',
        options: await _options());
    return _maps(result.data);
  }

  Future<List<Map<String, dynamic>>> bookings(String iid) async {
    final result = await _api.dio.get<dynamic>('${_base(iid)}/bookings',
        options: await _options());
    return _maps(result.data);
  }

  Future<Map<String, dynamic>> register(String iid, {
    required String kind, required String code, required String name,
    required String location, required int capacity,
  }) async {
    final result = await _api.dio.post<dynamic>('${_base(iid)}/resources',
        data: {'kind': kind, 'code': code, 'name': name,
          'location': location, 'capacity': capacity},
        options: await _options());
    return _map(result.data);
  }

  Future<Map<String, dynamic>> reserve(String iid, {
    required String resourceId, required String purpose,
    required DateTime startsAt, required DateTime endsAt,
  }) async {
    final result = await _api.dio.post<dynamic>('${_base(iid)}/bookings',
        data: {'resource_id': _id(resourceId), 'purpose': purpose,
          'starts_at': startsAt.toUtc().toIso8601String(),
          'ends_at': endsAt.toUtc().toIso8601String()},
        options: await _options());
    return _map(result.data);
  }

  Future<Map<String, dynamic>> cancel(String iid, String id, int version) async {
    final result = await _api.dio.post<dynamic>(
        '${_base(iid)}/bookings/${_id(id)}/cancel',
        data: {'expected_version': version}, options: await _options());
    return _map(result.data);
  }

  // Maintenance du campus : signalement accessible aux membres actifs,
  // changement d'état strictement administrateur côté API.
  Future<List<Map<String, dynamic>>> maintenanceTickets(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/maintenance',
        options: await _options());
    return _maps(r.data);
  }

  Future<Map<String, dynamic>> reportMaintenance(String iid,
      String resourceId, String description) async {
    final r = await _api.dio.post<dynamic>('${_base(iid)}/maintenance',
        data: {'resource_id': _id(resourceId), 'description': description},
        options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> transitionMaintenance(String iid, String ticketId,
      String action, int version, String note) async {
    if (!const {'start', 'resolve', 'dismiss'}.contains(action)) {
      throw ArgumentError.value(action, 'action', 'Transition invalide');
    }
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/maintenance/${_id(ticketId)}/$action',
        data: {'expected_version': version, 'note': note},
        options: await _options());
    return _map(r.data);
  }


  // Events reuse the existing institutional calendar. No tenant-local cache.
  Future<List<Map<String, dynamic>>> events(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/events',
        options: await _options());
    return _maps(r.data);
  }

  Future<List<Map<String, dynamic>>> myEventRegistrations(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/events/my-registrations',
        options: await _options());
    return _maps(r.data);
  }

  Future<Map<String, dynamic>> configureEventCapacity(
      String iid, String eventId, int version, int capacity) async {
    final r = await _api.dio.put<dynamic>(
        '${_base(iid)}/events/${_id(eventId)}/capacity',
        data: {'expected_version': version, 'capacity': capacity},
        options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> registerForEvent(String iid, String eventId) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/events/${_id(eventId)}/register',
        options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> withdrawFromEvent(
      String iid, String eventId, int registrationVersion) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/events/${_id(eventId)}/withdraw',
        data: {'expected_version': registrationVersion}, options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> publishCampusEvent(String iid, {
    required String title, required String details, required String location,
    required DateTime startsAt, required DateTime endsAt,
  }) async {
    final r = await _api.dio.post<dynamic>(
        '/v1/campus-operations/institutions/${_id(iid)}/calendar',
        data: {'kind': 'event', 'title': title, 'details': details,
          'location': location,
          'starts_at': startsAt.toUtc().toIso8601String(),
          'ends_at': endsAt.toUtc().toIso8601String()},
        options: await _options());
    return _map(r.data);
  }

  // Bibliothèque PHYSIQUE : distincte du catalogue de contenus numériques.
  Future<Map<String, dynamic>> physicalLibraryPolicy(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/library/policy',
        options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> updatePhysicalLibraryPolicy(String iid, {
    required int expectedVersion, required int loanDays,
    required int maxOpenLoans, required int maxRenewals,
    required int renewalDays,
  }) async {
    final r = await _api.dio.put<dynamic>('${_base(iid)}/library/policy',
        data: {'expected_version': expectedVersion, 'loan_days': loanDays,
          'max_open_loans': maxOpenLoans, 'max_renewals': maxRenewals,
          'renewal_days': renewalDays}, options: await _options());
    return _map(r.data);
  }

  Future<List<Map<String, dynamic>>> physicalBooks(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/library/books',
        options: await _options());
    return _maps(r.data);
  }

  Future<List<Map<String, dynamic>>> physicalCopies(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/library/copies',
        options: await _options());
    return _maps(r.data);
  }

  Future<List<Map<String, dynamic>>> physicalLoans(String iid) async {
    final r = await _api.dio.get<dynamic>('${_base(iid)}/library/loans',
        options: await _options());
    return _maps(r.data);
  }

  Future<Map<String, dynamic>> addPhysicalBook(String iid, {
    required String title, required String author, String isbn = '',
  }) async {
    final r = await _api.dio.post<dynamic>('${_base(iid)}/library/books',
        data: {'title': title, 'author': author, 'isbn': isbn},
        options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> addPhysicalCopy(String iid, {
    required String bookId, required String barcode,
  }) async {
    final r = await _api.dio.post<dynamic>('${_base(iid)}/library/copies',
        data: {'book_id': _id(bookId), 'barcode': barcode},
        options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> borrowPhysicalCopy(String iid, String copyId) async {
    final r = await _api.dio.post<dynamic>('${_base(iid)}/library/loans',
        data: {'copy_id': _id(copyId)}, options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> renewPhysicalLoan(String iid, String loanId,
      int expectedVersion) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/library/loans/${_id(loanId)}/renew',
        data: {'expected_version': expectedVersion}, options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> returnPhysicalLoan(String iid, String loanId,
      int expectedVersion) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/library/loans/${_id(loanId)}/return',
        data: {'expected_version': expectedVersion}, options: await _options());
    return _map(r.data);
  }


  Future<Map<String, dynamic>> reportPhysicalLoanIncident(String iid,
      String loanId, int expectedVersion, String condition) async {
    if (condition != 'lost' && condition != 'damaged') {
      throw ArgumentError.value(condition, 'condition', 'État invalide');
    }
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/library/loans/${_id(loanId)}/incident',
        data: {'expected_version': expectedVersion, 'condition': condition},
        options: await _options());
    return _map(r.data);
  }

  Future<Map<String, dynamic>> restoreDamagedPhysicalCopy(String iid,
      String copyId, int expectedVersion) async {
    final r = await _api.dio.post<dynamic>(
        '${_base(iid)}/library/copies/${_id(copyId)}/restore',
        data: {'expected_version': expectedVersion},
        options: await _options());
    return _map(r.data);
  }

}

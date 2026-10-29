import 'package:dio/dio.dart';
import '../../../core/database/app_database.dart';

import '../../../core/network/api_client.dart';
import '../application/identity_repository.dart';
import '../application/session_store.dart';
import '../domain/auth_session.dart';
import 'secure_session_store.dart';
import 'legacy_offline_files_stub.dart'
    if (dart.library.io) 'legacy_offline_files_native.dart' as legacy_files;

class ApiIdentityRepository implements IdentityRepository {
  ApiIdentityRepository({required ApiClient api, required SessionStore store, AppDatabase? database}) : _api = api, _store = store, _database = database;
  final ApiClient _api;
  final SessionStore _store;
  final AppDatabase? _database;

  Future<void> _assertLocalAccountOwnership(String accountId) async {
    final database = _database;
    if (database == null) return;
    final states = await database.select(database.localCloudSyncStates).get();
    if (states.any((state) => state.accountId != accountId)) {
      throw StateError('local_data_owned_by_another_account');
    }
    // A pre-ownership installation may contain personal SQLite data even if
    // cloud sync was never initialized. Do not silently claim it for a new user.
    // An authenticated legacy session is upgraded by SecureSessionStore.read().
    final owner = _store is SecureSessionStore
        ? await (_store as SecureSessionStore).ownerAccountId()
        : (await _store.read())?.accountId;
    if (owner != null) {
      if (owner != accountId) throw StateError('local_data_owned_by_another_account');
      return;
    }
    final tables = await database.customSelect(
      "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'local_%'",
    ).get();
    for (final table in tables) {
      final name = table.read<String>('name');
      if (!RegExp(r'^local_[a-z0-9_]+$').hasMatch(name)) continue;
      final count = await database.customSelect('SELECT 1 FROM "$name" LIMIT 1').get();
      if (count.isNotEmpty) throw StateError('unowned_legacy_local_data');
    }
    // Native downloaded files are not represented by SQLite on all legacy
    // installations. Reject an ownerless cache even when local tables are empty.
    if (await legacy_files.hasUnownedOfflineFiles()) {
      throw StateError('unowned_legacy_offline_files');
    }
  }

  Future<void> _saveVerifiedSession(AuthSession session) async {
    await _assertLocalAccountOwnership(session.accountId);
    await _store.save(session);
  }

  AuthSession _fromPayload(Map<String, dynamic> data) {
    final expires = DateTime.now().toUtc().add(Duration(seconds: data['expires_in_seconds'] as int));
    return AuthSession(
      accountId: data['account_id'] as String,
      displayName: data['display_name'] as String,
      accessToken: data['access_token'] as String,
      refreshToken: data['refresh_token'] as String,
      expiresAt: expires,
    );
  }

  @override
  Future<AuthSession?> currentSession() => _store.read();

  Future<Options> _authOptions() async {
    var session = await _store.read();
    if (session == null) throw StateError('authentication_required');
    if (session.accessExpired) session = await refresh();
    return Options(headers: {'Authorization': 'Bearer ${session.accessToken}'});
  }

  @override
  Future<AuthSession> login({required String login, required String password, String? deviceName}) async {
    final r = await _api.dio.post('/v1/identity/login', data: {'login': login, 'password': password, 'device_name': deviceName});
    final session = _fromPayload(Map<String, dynamic>.from(r.data));
    await _saveVerifiedSession(session);
    return session;
  }

  @override
  Future<AuthSession> register({required String displayName, required String password, String? email, String? phoneNumber, String? deviceName}) async {
    final r = await _api.dio.post('/v1/identity/register', data: {'display_name': displayName, 'password': password, 'email': email, 'phone_number': phoneNumber, 'device_name': deviceName});
    final session = _fromPayload(Map<String, dynamic>.from(r.data));
    await _saveVerifiedSession(session);
    return session;
  }

  @override
  Future<AuthSession> refresh() async {
    final current = await _store.read();
    if (current == null) throw StateError('not_authenticated');
    final r = await _api.dio.post('/v1/identity/refresh', data: {'refresh_token': current.refreshToken});
    final session = _fromPayload(Map<String, dynamic>.from(r.data));
    await _saveVerifiedSession(session);
    return session;
  }

  @override
  Future<void> logout() async {
    final current = await _store.read();
    try {
      if (current != null) await _api.dio.post('/v1/identity/logout', data: {'refresh_token': current.refreshToken});
    } on DioException {
      // Local logout remains authoritative for this device when network is unavailable.
    } finally {
      await _store.clear();
    }
  }


  @override
  Future<List<DeviceSession>> listSessions() async {
    final r = await _api.dio.get('/v1/identity/sessions', options: await _authOptions());
    return (r.data as List).map((e) {
      final m = Map<String, dynamic>.from(e);
      return DeviceSession(id: m['id'], deviceName: m['device_name'], createdAt: DateTime.parse(m['created_at']).toUtc(), expiresAt: DateTime.parse(m['expires_at']).toUtc(), active: m['active']);
    }).toList();
  }

  @override
  Future<void> revokeSession(String sessionId) async {
    await _api.dio.delete('/v1/identity/sessions/$sessionId', options: await _authOptions());
  }

  @override
  Future<void> logoutAll() async {
    await _api.dio.post('/v1/identity/logout-all', options: await _authOptions());
    await _store.clear();
  }

  @override
  Future<void> changePassword({required String currentPassword, required String newPassword}) async {
    await _api.dio.post('/v1/identity/change-password', data: {'current_password': currentPassword, 'new_password': newPassword}, options: await _authOptions());
    await _store.clear();
  }

  @override
  Future<String> requestPasswordRecovery(String login) async {
    final r = await _api.dio.post('/v1/identity/recovery/request', data: {'login': login});
    return Map<String, dynamic>.from(r.data)['challenge_id'] as String;
  }

  @override
  Future<void> confirmPasswordRecovery({required String challengeId, required String code, required String newPassword}) async {
    await _api.dio.post('/v1/identity/recovery/confirm', data: {'challenge_id': challengeId, 'code': code, 'new_password': newPassword});
  }

}

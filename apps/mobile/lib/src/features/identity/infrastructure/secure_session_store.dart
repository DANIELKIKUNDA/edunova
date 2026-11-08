import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../application/session_store.dart';
import '../domain/auth_session.dart';

class SecureSessionStore implements SessionStore {
  SecureSessionStore([FlutterSecureStorage? storage]) : _storage = storage ?? const FlutterSecureStorage();
  final FlutterSecureStorage _storage;

  // Serializes ownership changes across all store instances in this isolate.
  // The secure-storage plugin does not offer an atomic compare-and-set.
  static Future<void> _ownershipQueue = Future<void>.value();

  // Changes on login/logout invalidate in-flight repository operations.
  static int _sessionRevision = 0;
  static int get sessionRevision => _sessionRevision;

  static Future<T> _serialized<T>(Future<T> Function() operation) {
    final result = _ownershipQueue.then((_) => operation());
    _ownershipQueue = result.then<void>((_) {}, onError: (Object _, StackTrace __) {});
    return result;
  }

  static const _accountId = 'auth.accountId';
  // Installation owner survives logout: local SQLite projections are global.
  static const _localOwner = 'auth.localDataOwner';
  static const _displayName = 'auth.displayName';
  static const _access = 'auth.accessToken';
  static const _refresh = 'auth.refreshToken';
  static const _expires = 'auth.expiresAt';

  // Read the durable installation owner without exposing authentication tokens.
  Future<String?> ownerAccountId() => _serialized(() => _storage.read(key: _localOwner));

  @override
  Future<AuthSession?> read() => _serialized(() async {
    final accountId = await _storage.read(key: _accountId);
    final access = await _storage.read(key: _access);
    final refresh = await _storage.read(key: _refresh);
    final expires = await _storage.read(key: _expires);
    if (accountId == null || access == null || refresh == null || expires == null) return null;
    final owner = await _storage.read(key: _localOwner);
    if (owner != null && owner != accountId) {
      throw StateError('local_data_owned_by_another_account');
    }
    // Upgrade a valid legacy session before exposing any global local data.
    // A later logout must not leave its database available for another user.
    if (owner == null) {
      await _storage.write(key: _localOwner, value: accountId);
    }
    return AuthSession(
      accountId: accountId,
      displayName: await _storage.read(key: _displayName) ?? 'Étudiant EduNova',
      accessToken: access,
      refreshToken: refresh,
      expiresAt: DateTime.parse(expires).toUtc(),
    );
  });

  @override
  Future<void> save(AuthSession session) => _serialized(() async {
    final owner = await _storage.read(key: _localOwner);
    final existingAccount = await _storage.read(key: _accountId);
    if ((owner != null && owner != session.accountId) ||
        (existingAccount != null && existingAccount != session.accountId)) {
      throw StateError('local_data_owned_by_another_account');
    }
    // Write the owner first, before tokens. A failed write must not silently
    // authorize a different account to open global local projections.
    await _storage.write(key: _localOwner, value: session.accountId);
    // Avoid parallel partial writes of a token set during login/refresh.
    await _storage.write(key: _accountId, value: session.accountId);
    await _storage.write(key: _displayName, value: session.displayName);
    await _storage.write(key: _access, value: session.accessToken);
    await _storage.write(key: _refresh, value: session.refreshToken);
    await _storage.write(key: _expires, value: session.expiresAt.toUtc().toIso8601String());
    _sessionRevision++;
  });

  @override
  Future<void> clear() => _serialized(() async {
    // Preserve the installation owner, including when upgrading an older
    // installation that has an authenticated session but no owner marker.
    final owner = await _storage.read(key: _localOwner) ??
        await _storage.read(key: _accountId);
    if (owner != null && owner.isNotEmpty) {
      await _storage.write(key: _localOwner, value: owner);
    }
    // Invalidate outstanding operations before removing credentials.
    _sessionRevision++;
    for (final key in [_accountId, _displayName, _access, _refresh, _expires]) {
      await _storage.delete(key: key);
    }
  });
}

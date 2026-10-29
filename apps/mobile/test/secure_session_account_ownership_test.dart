import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:edunova/src/features/identity/domain/auth_session.dart';
import 'package:edunova/src/features/identity/infrastructure/secure_session_store.dart';

AuthSession session(String id) => AuthSession(
  accountId: id,
  displayName: 'Student $id',
  accessToken: 'access-$id',
  refreshToken: 'refresh-$id',
  expiresAt: DateTime.utc(2030, 1, 1),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() => FlutterSecureStorage.setMockInitialValues({}));

  test('logout retains ownership and blocks another account', () async {
    final store = SecureSessionStore();
    await store.save(session('alice'));
    await store.clear();
    expect(await store.read(), isNull);
    await expectLater(store.save(session('bob')), throwsStateError);
    await store.save(session('alice'));
    expect((await store.read())?.accountId, 'alice');
  });

  test('concurrent saves cannot claim the same installation twice', () async {
    final first = SecureSessionStore();
    final second = SecureSessionStore();
    final results = await Future.wait([
      first.save(session('alice')).then((_) => true, onError: (Object _) => false),
      second.save(session('bob')).then((_) => true, onError: (Object _) => false),
    ]);
    expect(results.where((value) => value).length, 1);
    final owner = (await first.read())?.accountId;
    expect(owner, anyOf('alice', 'bob'));
  });

  test('reading a legacy authenticated session immediately pins ownership', () async {
    FlutterSecureStorage.setMockInitialValues({
      'auth.accountId': 'legacy',
      'auth.accessToken': 'old-access',
      'auth.refreshToken': 'old-refresh',
      'auth.expiresAt': DateTime.utc(2030, 1, 1).toIso8601String(),
    });
    final store = SecureSessionStore();
    expect((await store.read())?.accountId, 'legacy');
    await store.clear();
    await expectLater(store.save(session('another')), throwsStateError);
  });

  test('legacy authenticated session is pinned on logout', () async {
    FlutterSecureStorage.setMockInitialValues({
      'auth.accountId': 'legacy',
      'auth.accessToken': 'old-access',
      'auth.refreshToken': 'old-refresh',
      'auth.expiresAt': DateTime.utc(2030, 1, 1).toIso8601String(),
    });
    final store = SecureSessionStore();
    await store.clear();
    await expectLater(store.save(session('another')), throwsStateError);
    await store.save(session('legacy'));
    expect((await store.read())?.accountId, 'legacy');
  });
}

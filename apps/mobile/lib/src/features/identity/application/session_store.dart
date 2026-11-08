import '../domain/auth_session.dart';

abstract class SessionStore {
  Future<AuthSession?> read();
  Future<void> save(AuthSession session);
  Future<void> clear();
}

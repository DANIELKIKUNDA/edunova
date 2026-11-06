import '../domain/auth_session.dart';

abstract class IdentityRepository {
  Future<AuthSession?> currentSession();
  Future<AuthSession> login({required String login, required String password, String? deviceName});
  Future<AuthSession> register({required String displayName, required String password, String? email, String? phoneNumber, String? deviceName});
  Future<AuthSession> refresh();
  Future<void> logout();
  Future<List<DeviceSession>> listSessions();
  Future<void> revokeSession(String sessionId);
  Future<void> logoutAll();
  Future<void> changePassword({required String currentPassword, required String newPassword});
  Future<String> requestPasswordRecovery(String login);
  Future<void> confirmPasswordRecovery({required String challengeId, required String code, required String newPassword});
}

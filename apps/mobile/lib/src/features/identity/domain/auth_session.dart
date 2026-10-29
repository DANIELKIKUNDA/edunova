class AuthSession {
  const AuthSession({
    required this.accountId,
    required this.displayName,
    required this.accessToken,
    required this.refreshToken,
    required this.expiresAt,
  });

  final String accountId;
  final String displayName;
  final String accessToken;
  final String refreshToken;
  final DateTime expiresAt;

  bool get accessExpired => !expiresAt.isAfter(DateTime.now().toUtc());
}

class DeviceSession {
  const DeviceSession({required this.id, required this.createdAt, required this.expiresAt, required this.active, this.deviceName});
  final String id;
  final String? deviceName;
  final DateTime createdAt;
  final DateTime expiresAt;
  final bool active;
}

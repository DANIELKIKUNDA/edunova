import '../domain/engagement.dart';

class NotificationTap {
  const NotificationTap({required this.deepLink, this.notificationId});
  final String deepLink;
  final String? notificationId;
}

abstract class LocalNotificationScheduler {
  bool get supportsSystemNotifications;
  Future<void> initialize();
  Future<bool> requestPermission();
  Future<void> schedule(LocalNotificationView notification);
  Future<void> cancel(String id);
  Future<void> cancelAll();
  Stream<NotificationTap> get interactions;
  Future<NotificationTap?> takeInitialInteraction();
}

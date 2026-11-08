import '../application/local_notification_scheduler.dart';
import '../domain/engagement.dart';

class UnsupportedLocalNotificationScheduler implements LocalNotificationScheduler {
  @override bool get supportsSystemNotifications => false;
  @override Future<void> initialize() async {}
  @override Future<bool> requestPermission() async => false;
  @override Future<void> schedule(LocalNotificationView notification) async {}
  @override Future<void> cancel(String id) async {}
  @override Future<void> cancelAll() async {}
  @override Stream<NotificationTap> get interactions => const Stream.empty();
  @override Future<NotificationTap?> takeInitialInteraction() async => null;
}
LocalNotificationScheduler createLocalNotificationScheduler()=>UnsupportedLocalNotificationScheduler();

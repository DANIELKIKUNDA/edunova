import '../domain/engagement.dart';

abstract class EngagementRepository {
  Stream<EngagementPreferences> watchPreferences();
  Future<EngagementPreferences> loadPreferences();
  Future<void> savePreferences(EngagementPreferences value);
  Stream<List<EngagementDailyStat>> watchRecentDays({int limit = 14});
  Future<void> recordActivity(EngagementDailyStat value);
  Future<EngagementDailyStat> recomputeToday(DateTime now);
  Stream<List<LocalNotificationView>> watchUpcomingNotifications({int limit = 20});
  Stream<List<LocalNotificationView>> watchNotificationHistory({int limit = 20});
  Future<void> markNotificationInteracted(String id);
  Future<StreakView> computeLocalStreak(DateTime now);
}

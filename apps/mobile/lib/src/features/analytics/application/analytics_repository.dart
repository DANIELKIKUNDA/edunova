import '../domain/analytics.dart';
abstract interface class AnalyticsRepository {
  Future<AnalyticsSnapshot> buildSnapshot(DateTime now);
  Stream<List<RecommendationFeedback>> watchFeedback();
  Future<void> saveFeedback(RecommendationFeedback feedback);
}

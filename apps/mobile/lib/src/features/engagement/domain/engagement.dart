class EngagementPreferences {
  const EngagementPreferences({
    this.quietStartMinute = 1320,
    this.quietEndMinute = 420,
    this.maxDailyNotifications = 2,
    this.preferredStudyMinute = 1140,
    this.assessmentEnabled = true,
    this.studyPlanEnabled = true,
    this.flashcardsEnabled = true,
    this.streakEnabled = false,
    this.contentEnabled = true,
    this.pushEnabled = true,
    this.timezoneOffsetMinutes = 0,
    this.dailyGoalMinutes = 30,
  });

  final int quietStartMinute;
  final int quietEndMinute;
  final int maxDailyNotifications;
  final int preferredStudyMinute;
  final bool assessmentEnabled;
  final bool studyPlanEnabled;
  final bool flashcardsEnabled;
  final bool streakEnabled;
  final bool contentEnabled;
  final bool pushEnabled;
  final int timezoneOffsetMinutes;
  final int dailyGoalMinutes;

  EngagementPreferences copyWith({
    int? quietStartMinute,
    int? quietEndMinute,
    int? maxDailyNotifications,
    int? preferredStudyMinute,
    bool? assessmentEnabled,
    bool? studyPlanEnabled,
    bool? flashcardsEnabled,
    bool? streakEnabled,
    bool? contentEnabled,
    bool? pushEnabled,
    int? timezoneOffsetMinutes,
    int? dailyGoalMinutes,
  }) => EngagementPreferences(
    quietStartMinute: quietStartMinute ?? this.quietStartMinute,
    quietEndMinute: quietEndMinute ?? this.quietEndMinute,
    maxDailyNotifications: maxDailyNotifications ?? this.maxDailyNotifications,
    preferredStudyMinute: preferredStudyMinute ?? this.preferredStudyMinute,
    assessmentEnabled: assessmentEnabled ?? this.assessmentEnabled,
    studyPlanEnabled: studyPlanEnabled ?? this.studyPlanEnabled,
    flashcardsEnabled: flashcardsEnabled ?? this.flashcardsEnabled,
    streakEnabled: streakEnabled ?? this.streakEnabled,
    contentEnabled: contentEnabled ?? this.contentEnabled,
    pushEnabled: pushEnabled ?? this.pushEnabled,
    timezoneOffsetMinutes: timezoneOffsetMinutes ?? this.timezoneOffsetMinutes,
    dailyGoalMinutes: dailyGoalMinutes ?? this.dailyGoalMinutes,
  );
}

class EngagementDailyStat {
  const EngagementDailyStat({required this.dayKey, this.activeMinutes = 0, this.completedTasks = 0, this.quizQuestions = 0, this.flashcardsReviewed = 0});
  final String dayKey;
  final int activeMinutes;
  final int completedTasks;
  final int quizQuestions;
  final int flashcardsReviewed;
  bool get active => activeMinutes > 0 || completedTasks > 0 || quizQuestions > 0 || flashcardsReviewed > 0;
}

class StreakView {
  const StreakView({required this.currentDays, required this.bestDays, required this.weeklyActiveDays, required this.weeklyMinutes, this.lastActiveDay});
  final int currentDays;
  final int bestDays;
  final int weeklyActiveDays;
  final int weeklyMinutes;
  final String? lastActiveDay;
}

class LocalNotificationView {
  const LocalNotificationView({required this.id, required this.eventId, required this.fireAt, required this.title, required this.body, required this.category, required this.status, this.dedupeKey, this.expiresAt, this.deepLink = '', this.priority = 50});
  final String id;
  final String eventId;
  final String? dedupeKey;
  final DateTime fireAt;
  final DateTime? expiresAt;
  final String title;
  final String body;
  final String category;
  final String status;
  final String deepLink;
  final int priority;
}

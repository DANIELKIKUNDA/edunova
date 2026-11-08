enum AnalyticsTrend { improving, stable, declining }
enum AnalyticsEvidence { limited, moderate, strong }
enum AnalyticsRisk { high, medium, low }
enum RecommendationKind { assessmentFocus, recoverErrors, quizDrill, flashcardReview, continueCourse, planRecovery }

class DailyLearningPoint {
  const DailyLearningPoint({required this.day,required this.studyMinutes,required this.completedTasks,required this.quizQuestions,required this.flashcardsReviewed});
  final DateTime day;
  final int studyMinutes,completedTasks,quizQuestions,flashcardsReviewed;
  bool get active => studyMinutes>0||completedTasks>0||quizQuestions>0||flashcardsReviewed>0;
}

class CourseAnalyticsSignal {
  const CourseAnalyticsSignal({required this.courseId,required this.title,this.coverage,this.quizMastery,this.flashcardMastery,this.weaknessRecovery,this.openErrors=0,this.overdueFlashcards=0,this.daysToNextAssessment,this.nextAssessmentReadiness,this.studyMinutes7d=0,this.planAdherence7d,this.masteryDelta7d});
  final String courseId,title;
  final double? coverage,quizMastery,flashcardMastery,weaknessRecovery,planAdherence7d,masteryDelta7d;
  final int openErrors,overdueFlashcards,studyMinutes7d;
  final int? daysToNextAssessment,nextAssessmentReadiness;
}

class AnalyticsSnapshot {
  const AnalyticsSnapshot({required this.generatedAt,required this.studyMinutes7d,required this.studyMinutesPrev7d,required this.activeDays7d,required this.streakDays,required this.courses,this.quizAccuracy7d,this.quizAccuracyPrev7d,this.planAdherence7d,this.activity14d=const []});
  final DateTime generatedAt;
  final int studyMinutes7d,studyMinutesPrev7d,activeDays7d,streakDays;
  final double? quizAccuracy7d,quizAccuracyPrev7d,planAdherence7d;
  final List<CourseAnalyticsSignal> courses;
  final List<DailyLearningPoint> activity14d;
}

class TrendMetric {
  const TrendMetric(this.current,this.previous,this.delta,this.direction);
  final double current,previous,delta;
  final AnalyticsTrend direction;
}

class CourseInsight {
  const CourseInsight({required this.courseId,required this.title,required this.risk,required this.focusReason,required this.direction,this.readiness,this.coverage,this.quizMastery,this.flashcardMastery,this.weaknessRecovery,this.openErrors=0,this.overdueFlashcards=0,this.daysToNextAssessment,this.studyMinutes7d=0});
  final String courseId,title,focusReason;
  final int? readiness,daysToNextAssessment;
  final int openErrors,overdueFlashcards,studyMinutes7d;
  final double? coverage,quizMastery,flashcardMastery,weaknessRecovery;
  final AnalyticsRisk risk;
  final AnalyticsTrend direction;
}

class StudyRecommendation {
  const StudyRecommendation({required this.id,required this.kind,required this.title,required this.reason,required this.recommendedMinutes,required this.priorityScore,required this.deepLink,this.courseId,this.courseTitle});
  final String id,title,reason,deepLink;
  final RecommendationKind kind;
  final String? courseId,courseTitle;
  final int recommendedMinutes,priorityScore;
}

class AnalyticsReport {
  const AnalyticsReport({required this.generatedAt,required this.momentum,required this.evidence,required this.studyTime,required this.activeDays7d,required this.streakDays,required this.courseInsights,required this.recommendations,required this.explanation,this.quizAccuracy,this.planAdherence7d,this.activity14d=const []});
  final DateTime generatedAt;
  final AnalyticsTrend momentum;
  final AnalyticsEvidence evidence;
  final TrendMetric studyTime;
  final TrendMetric? quizAccuracy;
  final int activeDays7d,streakDays;
  final double? planAdherence7d;
  final List<DailyLearningPoint> activity14d;
  final List<CourseInsight> courseInsights;
  final List<StudyRecommendation> recommendations;
  final String explanation;
  int get recommendedMinutes => recommendations.fold(0,(sum,r)=>sum+r.recommendedMinutes);
}

enum RecommendationFeedbackState { snoozed, completed, dismissed }
class RecommendationFeedback {
  const RecommendationFeedback({required this.recommendationId,required this.state,required this.updatedAt,this.snoozedUntil});
  final String recommendationId;
  final RecommendationFeedbackState state;
  final DateTime? snoozedUntil;
  final DateTime updatedAt;
}

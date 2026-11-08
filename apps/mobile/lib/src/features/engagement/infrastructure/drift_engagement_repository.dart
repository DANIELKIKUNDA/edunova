import 'package:drift/drift.dart';
import '../../../core/security/local_account_access.dart';

import '../../../core/database/app_database.dart';
import '../application/engagement_repository.dart';
import '../domain/engagement.dart';

class DriftEngagementRepository implements EngagementRepository {
  DriftEngagementRepository(this.db);
  final AppDatabase db;
  final LocalAccountAccess _access = LocalAccountAccess();

  @override
  Stream<EngagementPreferences> watchPreferences() {
    return _access.protect((db.select(db.localEngagementPreferences)..where((t) => t.id.equals('current'))).watchSingleOrNull().map(_prefs));
  }

  EngagementPreferences _prefs(LocalEngagementPreference? row) => row == null ? EngagementPreferences(timezoneOffsetMinutes: DateTime.now().timeZoneOffset.inMinutes) : EngagementPreferences(
    quietStartMinute: row.quietStartMinute,
    quietEndMinute: row.quietEndMinute,
    maxDailyNotifications: row.maxDailyNotifications,
    preferredStudyMinute: row.preferredStudyMinute,
    assessmentEnabled: row.assessmentEnabled,
    studyPlanEnabled: row.studyPlanEnabled,
    flashcardsEnabled: row.flashcardsEnabled,
    streakEnabled: row.streakEnabled,
    contentEnabled: row.contentEnabled,
    pushEnabled: row.pushEnabled,
    timezoneOffsetMinutes: row.timezoneOffsetMinutes,
    dailyGoalMinutes: row.dailyGoalMinutes,
  );

  @override
  Future<EngagementPreferences> loadPreferences() async {
    await _access.assertOwned();
    return _prefs(await (db.select(db.localEngagementPreferences)..where((t) => t.id.equals('current'))).getSingleOrNull());
  }

  @override
  Future<void> savePreferences(EngagementPreferences p) async {
    await _access.assertOwned();
    await db.into(db.localEngagementPreferences).insertOnConflictUpdate(LocalEngagementPreferencesCompanion.insert(
      id: const Value('current'),
      quietStartMinute: Value(p.quietStartMinute), quietEndMinute: Value(p.quietEndMinute),
      maxDailyNotifications: Value(p.maxDailyNotifications), preferredStudyMinute: Value(p.preferredStudyMinute),
      assessmentEnabled: Value(p.assessmentEnabled), studyPlanEnabled: Value(p.studyPlanEnabled),
      flashcardsEnabled: Value(p.flashcardsEnabled), streakEnabled: Value(p.streakEnabled),
      contentEnabled: Value(p.contentEnabled), pushEnabled: Value(p.pushEnabled), timezoneOffsetMinutes: Value(p.timezoneOffsetMinutes), dailyGoalMinutes: Value(p.dailyGoalMinutes), updatedAt: DateTime.now(),
    ));
  }

  @override
  Stream<List<EngagementDailyStat>> watchRecentDays({int limit = 14}) {
    final q = db.select(db.localEngagementDailyStats)..orderBy([(t) => OrderingTerm.desc(t.dayKey)])..limit(limit);
    return _access.protect(q.watch().map((rows) => rows.map((r) => EngagementDailyStat(dayKey:r.dayKey,activeMinutes:r.activeMinutes,completedTasks:r.completedTasks,quizQuestions:r.quizQuestions,flashcardsReviewed:r.flashcardsReviewed)).toList()));
  }

  @override
  Future<void> recordActivity(EngagementDailyStat v) async {
    await _access.assertOwned();
    final old = await (db.select(db.localEngagementDailyStats)..where((t) => t.dayKey.equals(v.dayKey))).getSingleOrNull();
    await db.into(db.localEngagementDailyStats).insertOnConflictUpdate(LocalEngagementDailyStatsCompanion.insert(
      dayKey: v.dayKey,
      activeMinutes: Value(v.activeMinutes > (old?.activeMinutes ?? 0) ? v.activeMinutes : (old?.activeMinutes ?? 0)),
      completedTasks: Value(v.completedTasks > (old?.completedTasks ?? 0) ? v.completedTasks : (old?.completedTasks ?? 0)),
      quizQuestions: Value(v.quizQuestions > (old?.quizQuestions ?? 0) ? v.quizQuestions : (old?.quizQuestions ?? 0)),
      flashcardsReviewed: Value(v.flashcardsReviewed > (old?.flashcardsReviewed ?? 0) ? v.flashcardsReviewed : (old?.flashcardsReviewed ?? 0)),
      updatedAt: DateTime.now(),
    ));
  }


  @override
  Future<EngagementDailyStat> recomputeToday(DateTime now) async {
    await _access.assertOwned();
    final start=DateTime(now.year,now.month,now.day);
    final end=start.add(const Duration(days:1));
    final quiz=await (db.select(db.localQuizAnswers)..where((t)=>t.answeredAt.isBiggerOrEqualValue(start) & t.answeredAt.isSmallerThanValue(end))).get();
    final flash=await (db.select(db.localFlashcardReviewEvents)..where((t)=>t.reviewedAt.isBiggerOrEqualValue(start) & t.reviewedAt.isSmallerThanValue(end))).get();
    final sessions=await (db.select(db.localStudySessions)..where((t)=>t.startedAt.isBiggerOrEqualValue(start) & t.startedAt.isSmallerThanValue(end))).get();
    final completed=await (db.select(db.localAdaptiveStudyBlocks)..where((t)=>t.status.equals('completed') & t.updatedAt.isBiggerOrEqualValue(start) & t.updatedAt.isSmallerThanValue(end))).get();
    final minutes=sessions.fold<int>(0,(a,b)=>a+b.actualMinutes);
    final day=EngagementDailyStat(dayKey:'${start.year.toString().padLeft(4,'0')}-${start.month.toString().padLeft(2,'0')}-${start.day.toString().padLeft(2,'0')}',activeMinutes:minutes,completedTasks:completed.length,quizQuestions:quiz.length,flashcardsReviewed:flash.length);
    await recordActivity(day);
    return day;
  }

  @override
  Stream<List<LocalNotificationView>> watchUpcomingNotifications({int limit = 20}) {
    final q=db.select(db.localNotificationIntents)
      ..where((t)=>t.status.equals('planned') & t.fireAt.isBiggerOrEqualValue(DateTime.now()))
      ..orderBy([(t)=>OrderingTerm.asc(t.fireAt)])
      ..limit(limit);
    return _access.protect(q.watch().map((rows)=>rows.map((r)=>LocalNotificationView(id:r.id,eventId:r.eventId,dedupeKey:r.dedupeKey,fireAt:r.fireAt,expiresAt:r.expiresAt,title:r.title,body:r.body,category:r.category,status:r.status,deepLink:r.deepLink,priority:r.priority)).toList()));
  }

  @override
  Stream<List<LocalNotificationView>> watchNotificationHistory({int limit = 20}) {
    final q=db.select(db.localNotificationIntents)
      ..where((t)=>t.fireAt.isSmallerThanValue(DateTime.now()) | t.status.equals('opened'))
      ..orderBy([(t)=>OrderingTerm.desc(t.fireAt)])
      ..limit(limit);
    return _access.protect(q.watch().map((rows)=>rows.map((r)=>LocalNotificationView(id:r.id,eventId:r.eventId,dedupeKey:r.dedupeKey,fireAt:r.fireAt,expiresAt:r.expiresAt,title:r.title,body:r.body,category:r.category,status:r.status,deepLink:r.deepLink,priority:r.priority)).toList()));
  }

  @override
  Future<void> markNotificationInteracted(String id) async {
    await _access.assertOwned();
    await (db.update(db.localNotificationIntents)..where((t)=>t.id.equals(id))).write(LocalNotificationIntentsCompanion(status:const Value('opened'),interactedAt:Value(DateTime.now())));
  }

  @override
  Future<StreakView> computeLocalStreak(DateTime now) async {
    await _access.assertOwned();
    final rows=await (db.select(db.localEngagementDailyStats)..orderBy([(t)=>OrderingTerm.asc(t.dayKey)])).get();
    final active=rows.where((r)=>r.activeMinutes>0||r.completedTasks>0||r.quizQuestions>0||r.flashcardsReviewed>0).toList();
    if(active.isEmpty) return const StreakView(currentDays:0,bestDays:0,weeklyActiveDays:0,weeklyMinutes:0);
    final dates=active.map((r)=>DateTime.parse(r.dayKey)).toList();
    var best=1, run=1;
    for(var i=1;i<dates.length;i++){
      if(dates[i].difference(dates[i-1]).inDays==1){run++; if(run>best)best=run;} else if(dates[i]!=dates[i-1]){run=1;}
    }
    final set=dates.map((d)=>DateTime(d.year,d.month,d.day)).toSet();
    var cursor=DateTime(now.year,now.month,now.day); if(!set.contains(cursor)) cursor=cursor.subtract(const Duration(days:1));
    var current=0; while(set.contains(cursor)){current++; cursor=cursor.subtract(const Duration(days:1));}
    final start=DateTime(now.year,now.month,now.day).subtract(const Duration(days:6));
    final weekly=active.where((r)=>!DateTime.parse(r.dayKey).isBefore(start)).toList();
    return StreakView(currentDays:current,bestDays:best,weeklyActiveDays:weekly.length,weeklyMinutes:weekly.fold(0,(a,b)=>a+b.activeMinutes),lastActiveDay:active.last.dayKey);
  }
}

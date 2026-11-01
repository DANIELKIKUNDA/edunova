import 'package:drift/drift.dart';
import '../../../core/security/local_account_access.dart';

import '../../../core/database/app_database.dart';
import '../application/analytics_repository.dart';
import '../domain/analytics.dart';

class DriftAnalyticsRepository implements AnalyticsRepository {
  DriftAnalyticsRepository(this.db);
  final AppDatabase db;
  final LocalAccountAccess _access = LocalAccountAccess();

  DateTime _day(DateTime d) => DateTime(d.year,d.month,d.day);
  String _dayKey(DateTime d) => '${d.year.toString().padLeft(4,'0')}-${d.month.toString().padLeft(2,'0')}-${d.day.toString().padLeft(2,'0')}';
  double? _ratio(int numerator,int denominator)=>denominator<=0?null:numerator/denominator;

  @override
  Future<AnalyticsSnapshot> buildSnapshot(DateTime now) async {
    await _access.assertOwned();
    final today=_day(now);
    final start7=today.subtract(const Duration(days:6));
    final startPrev=today.subtract(const Duration(days:13));
    final endPrev=start7;

    final days=await db.select(db.localEngagementDailyStats).get();
    final currentDays=days.where((r){final d=DateTime.tryParse(r.dayKey);return d!=null&&!d.isBefore(start7);}).toList();
    final previousDays=days.where((r){final d=DateTime.tryParse(r.dayKey);return d!=null&&!d.isBefore(startPrev)&&d.isBefore(endPrev);}).toList();
    final study7=currentDays.fold<int>(0,(a,b)=>a+b.activeMinutes);
    final studyPrev=previousDays.fold<int>(0,(a,b)=>a+b.activeMinutes);
    final active7=currentDays.where((d)=>d.activeMinutes>0||d.completedTasks>0||d.quizQuestions>0||d.flashcardsReviewed>0).length;
    final activeDates=days.where((d)=>d.activeMinutes>0||d.completedTasks>0||d.quizQuestions>0||d.flashcardsReviewed>0).map((d)=>DateTime.tryParse(d.dayKey)).whereType<DateTime>().map(_day).toSet();
    var cursor=today; if(!activeDates.contains(cursor))cursor=cursor.subtract(const Duration(days:1)); var streak=0; while(activeDates.contains(cursor)){streak++;cursor=cursor.subtract(const Duration(days:1));}

    final attempts=await db.select(db.localQuizAttempts).get();
    bool inCurrent(DateTime d)=>!d.isBefore(start7)&&d.isBefore(today.add(const Duration(days:1)));
    bool inPrevious(DateTime d)=>!d.isBefore(startPrev)&&d.isBefore(endPrev);
    double? attemptAccuracy(Iterable<LocalQuizAttempt> rows){final total=rows.fold<int>(0,(a,b)=>a+b.totalQuestions);final correct=rows.fold<int>(0,(a,b)=>a+b.correctQuestions);return _ratio(correct,total);}
    final quiz7=attemptAccuracy(attempts.where((a)=>inCurrent(a.completedAt)));
    final quizPrev=attemptAccuracy(attempts.where((a)=>inPrevious(a.completedAt)));

    final sessions=await db.select(db.localStudySessions).get();
    final currentSessions=sessions.where((s)=>inCurrent(s.startedAt)).toList();
    final planned=currentSessions.fold<int>(0,(a,b)=>a+b.plannedMinutes);
    final actual=currentSessions.fold<int>(0,(a,b)=>a+b.actualMinutes);
    final adherence=planned<=0?null:(actual/planned).clamp(0.0,1.0).toDouble();

    final courseRows=await db.select(db.localCourseRecords).get();
    final libraryRows=await db.select(db.localLibraryCourses).get();
    final titleByCourse=<String,String>{for(final c in libraryRows)c.id:c.title,for(final c in courseRows)c.id:c.title};
    final coverageByCourse=<String,double>{for(final c in courseRows)c.id:c.progress.clamp(0.0,1.0).toDouble()};
    final errors=await db.select(db.localErrorLedgerItems).get();
    final cards=await db.select(db.localFlashcards).get();
    final states=await db.select(db.localFlashcardStates).get();
    final stateById={for(final s in states)s.flashcardId:s};
    final events=await (db.select(db.localAcademicEvents)..where((t)=>t.isActive.equals(true) & t.startsAt.isBiggerOrEqualValue(now))..orderBy([(t)=>OrderingTerm.asc(t.startsAt)])).get();

    final courseIds=<String>{...titleByCourse.keys,...attempts.map((a)=>a.courseId),...errors.map((e)=>e.courseId),...cards.map((c)=>c.courseId),...currentSessions.map((s)=>s.courseId),...events.map((e)=>e.courseId).whereType<String>()};
    final signals=<CourseAnalyticsSignal>[];
    for(final courseId in courseIds){
      final title=titleByCourse[courseId]??'Cours';
      final courseAttempts7=attempts.where((a)=>a.courseId==courseId&&inCurrent(a.completedAt));
      final courseAttemptsPrev=attempts.where((a)=>a.courseId==courseId&&inPrevious(a.completedAt));
      final qm=attemptAccuracy(courseAttempts7); final qPrev=attemptAccuracy(courseAttemptsPrev);
      final courseErrors=errors.where((e)=>e.courseId==courseId).toList();
      final open=courseErrors.where((e)=>e.recoveredAt==null).length;
      final recovery=courseErrors.isEmpty?null:courseErrors.where((e)=>e.recoveredAt!=null).length/courseErrors.length;
      final courseCards=cards.where((c)=>c.courseId==courseId).toList();
      final mastered=courseCards.where((c)=>(stateById[c.id]?.repetitions??0)>=2).length;
      final fm=courseCards.isEmpty?null:mastered/courseCards.length;
      final overdue=courseCards.where((c){final due=stateById[c.id]?.dueAt;return due!=null&&!due.isAfter(now);}).length;
      final matchingEvents=events.where((e)=>e.courseId==courseId).toList();
      final next=matchingEvents.isEmpty?null:matchingEvents.first;
      final daysTo=next==null?null:((next.startsAt.difference(today).inHours)/24).ceil().clamp(0,3650).toInt();
      final courseMinutes=currentSessions.where((s)=>s.courseId==courseId).fold<int>(0,(a,b)=>a+b.actualMinutes);
      final delta=qm!=null&&qPrev!=null?qm-qPrev:null;
      signals.add(CourseAnalyticsSignal(courseId:courseId,title:title,coverage:coverageByCourse[courseId],quizMastery:qm,flashcardMastery:fm,weaknessRecovery:recovery,openErrors:open,overdueFlashcards:overdue,daysToNextAssessment:daysTo,studyMinutes7d:courseMinutes,planAdherence7d:adherence,masteryDelta7d:delta));
    }

    final dayByKey={for(final d in days)d.dayKey:d};
    final activity14d=<DailyLearningPoint>[];
    for(var offset=13;offset>=0;offset--){
      final day=today.subtract(Duration(days:offset));
      final row=dayByKey[_dayKey(day)];
      activity14d.add(DailyLearningPoint(day:day,studyMinutes:row?.activeMinutes??0,completedTasks:row?.completedTasks??0,quizQuestions:row?.quizQuestions??0,flashcardsReviewed:row?.flashcardsReviewed??0));
    }
    final snapshot=AnalyticsSnapshot(generatedAt:now,studyMinutes7d:study7,studyMinutesPrev7d:studyPrev,quizAccuracy7d:quiz7,quizAccuracyPrev7d:quizPrev,planAdherence7d:adherence,activeDays7d:active7,streakDays:streak,courses:signals,activity14d:activity14d);
    await _persistDailySignals(snapshot);
    return snapshot;
  }

  Future<void> _persistDailySignals(AnalyticsSnapshot snapshot) async {
    final day=_dayKey(snapshot.generatedAt);
    for(final c in snapshot.courses){
      int? readiness;
      final vals=<({double v,double w})>[]; if(c.coverage!=null)vals.add((v:c.coverage!,w:.30));if(c.quizMastery!=null)vals.add((v:c.quizMastery!,w:.40));if(c.flashcardMastery!=null)vals.add((v:c.flashcardMastery!,w:.15));if(c.weaknessRecovery!=null)vals.add((v:c.weaknessRecovery!,w:.15)); if(vals.isNotEmpty){final w=vals.fold(0.0,(a,b)=>a+b.w);readiness=(vals.fold(0.0,(a,b)=>a+b.v*b.w)/w*100).round();}
      await db.into(db.localAnalyticsCourseSnapshots).insertOnConflictUpdate(LocalAnalyticsCourseSnapshotsCompanion.insert(courseId:c.courseId,dayKey:day,readiness:Value(readiness),quizMastery:Value(c.quizMastery),coverage:Value(c.coverage),openErrors:Value(c.openErrors),studyMinutes:Value(c.studyMinutes7d),generatedAt:snapshot.generatedAt));
    }
  }

  @override
  Stream<List<RecommendationFeedback>> watchFeedback(){
    return _access.protect(db.select(db.localAnalyticsRecommendationFeedback).watch().map((rows)=>rows.map((r)=>RecommendationFeedback(recommendationId:r.recommendationId,state:RecommendationFeedbackState.values.byName(r.state),snoozedUntil:r.snoozedUntil,updatedAt:r.updatedAt)).toList()));
  }

  @override
  Future<void> saveFeedback(RecommendationFeedback f) async {
    await _access.assertOwned();
    await db.into(db.localAnalyticsRecommendationFeedback).insertOnConflictUpdate(LocalAnalyticsRecommendationFeedbackCompanion.insert(recommendationId:f.recommendationId,state:f.state.name,snoozedUntil:Value(f.snoozedUntil),updatedAt:f.updatedAt));
  }
}

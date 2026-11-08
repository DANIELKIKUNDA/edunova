import '../domain/adaptive_planning.dart';
import '../domain/study_plan.dart';
import 'adaptive_planning_repository.dart';

class GenerateAdaptiveTodayPlan {
  const GenerateAdaptiveTodayPlan({
    required this.studyRepository,
    required this.adaptiveRepository,
    this.engine = const AdaptivePlanningEngine(),
  });

  final StudyPlanRepository studyRepository;
  final AdaptivePlanningRepository adaptiveRepository;
  final AdaptivePlanningEngine engine;

  Future<AdaptiveDayPlan> call({required DateTime now, int? budgetOverride}) async {
    final prefs=await adaptiveRepository.loadPreferences();
    final debts=await adaptiveRepository.loadDebts();
    final snapshots=await studyRepository.loadSnapshots();
    final events=await studyRepository.watchUpcomingEvents().first;
    final timetable=await studyRepository.watchTimetable().first;
    final rules=await adaptiveRepository.watchAvailabilityRules().first;

    final nearest=<String,AcademicEvent>{};
    for(final e in events.where((e)=>e.courseId!=null&&e.startsAt.isAfter(now))){
      final current=nearest[e.courseId!];
      if(current==null||e.startsAt.isBefore(current.startsAt)) nearest[e.courseId!]=e;
    }

    final states=<String,AdaptiveCourseState>{};
    final tasks=<AdaptiveStudyTask>[];
    for(final s in snapshots){
      final debt=debts[s.courseId];
      states[s.courseId]=AdaptiveCourseState(
        courseId:s.courseId,readiness:s.readiness,openErrors:s.openErrors,dueFlashcards:s.dueFlashcards,
        overdueMinutes:debt?.overdueMinutes??0,
      );
      final deadline=nearest[s.courseId]?.startsAt;
      final importance=_importance(nearest[s.courseId]?.kind);
      if(s.openErrors>0){tasks.add(AdaptiveStudyTask(id:'errors:${s.courseId}',courseId:s.courseId,title:'Revoir mes erreurs · ${s.title}',kind:StudyTaskKind.errors,remainingMinutes:(s.openErrors*4).clamp(10,40).toInt(),learningValue:1,cognitiveLoad:4,deadline:deadline,importance:importance,deferredCount:debt?.deferredCount??0));}
      if(s.dueFlashcards>0){tasks.add(AdaptiveStudyTask(id:'flash:${s.courseId}',courseId:s.courseId,title:'Flashcards · ${s.title}',kind:StudyTaskKind.flashcards,remainingMinutes:s.dueFlashcards.clamp(8,30).toInt(),learningValue:.85,cognitiveLoad:2,deadline:deadline,importance:importance));}
      if(s.hasQuiz){tasks.add(AdaptiveStudyTask(id:'quiz:${s.courseId}',courseId:s.courseId,title:'Quiz ciblé · ${s.title}',kind:StudyTaskKind.quiz,remainingMinutes:20,learningValue:.95,cognitiveLoad:4,deadline:deadline,importance:importance));}
      if(s.hasSummary){tasks.add(AdaptiveStudyTask(id:'summary:${s.courseId}',courseId:s.courseId,title:'Résumé actif · ${s.title}',kind:StudyTaskKind.summary,remainingMinutes:15,learningValue:.7,cognitiveLoad:2,deadline:deadline,importance:importance));}
      tasks.add(AdaptiveStudyTask(id:'read:${s.courseId}',courseId:s.courseId,title:'Continuer ${s.title}',kind:StudyTaskKind.read,remainingMinutes:30,learningValue:.6,cognitiveLoad:3,deadline:deadline,importance:importance));
    }

    var windows=_todayWindows(now,rules);
    windows=_subtractTimetable(now,windows,timetable);
    final requested=budgetOverride??prefs.dailyBudgetMinutes;
    if(windows.isEmpty){
      windows=[AvailabilityWindow(id:'immediate',startsAt:now,endsAt:now.add(Duration(minutes:requested)),energy:EnergyLevel.medium)];
    }else if(budgetOverride!=null){
      windows=_capWindows(windows,requested);
    }
    final plan=engine.buildDay(
      now:now,windows:windows,states:states,tasks:tasks,
      constraints:AdvancedPlanningConstraints(
        maxContinuousMinutes:prefs.maxContinuousMinutes,breakMinutes:prefs.breakMinutes,
        maxCoursesPerDay:prefs.maxCoursesPerDay,maxCourseSwitches:prefs.maxCourseSwitches,
        targetReadiness:prefs.targetReadiness,
      ),
    );
    await adaptiveRepository.replaceTodayBlocks(plan.blocks,now,reason:budgetOverride==null?'automatic':'timebox:$requested');
    return plan;
  }


  Future<AdaptiveDayPlan> emergency({required DateTime now, required AcademicEvent event, int budgetMinutes = 60}) async {
    if(event.courseId==null) throw StateError('Une évaluation urgente doit être liée à un cours.');
    final snapshots=await studyRepository.loadSnapshots();
    CoursePlanningSnapshot? state;
    for(final row in snapshots){if(row.courseId==event.courseId){state=row;break;}}
    if(state==null) throw StateError('Aucune donnée de progression pour ce cours.');
    final importance=event.kind==AcademicEventKind.exam?AssessmentImportance.critical:AssessmentImportance.high;
    final tasks=<AdaptiveStudyTask>[
      AdaptiveStudyTask(id:'emergency:${event.id}:diag',courseId:state.courseId,title:'Diagnostic rapide',kind:StudyTaskKind.diagnostic,remainingMinutes:10,learningValue:1,cognitiveLoad:4,deadline:event.startsAt,importance:importance,pinned:true),
      if(state.hasSummary) AdaptiveStudyTask(id:'emergency:${event.id}:summary',courseId:state.courseId,title:'Points essentiels',kind:StudyTaskKind.summary,remainingMinutes:12,learningValue:.9,cognitiveLoad:2,deadline:event.startsAt,importance:importance),
      if(state.openErrors>0) AdaptiveStudyTask(id:'emergency:${event.id}:errors',courseId:state.courseId,title:'Revoir mes erreurs',kind:StudyTaskKind.errors,remainingMinutes:15,learningValue:1,cognitiveLoad:4,deadline:event.startsAt,importance:importance),
      if(state.hasQuiz) AdaptiveStudyTask(id:'emergency:${event.id}:quiz',courseId:state.courseId,title:'Quiz ciblé',kind:StudyTaskKind.quiz,remainingMinutes:15,learningValue:1,cognitiveLoad:4,deadline:event.startsAt,importance:importance),
      AdaptiveStudyTask(id:'emergency:${event.id}:mock',courseId:state.courseId,title:'Mini examen blanc',kind:StudyTaskKind.mockExam,remainingMinutes:20,learningValue:1,cognitiveLoad:5,minChunkMinutes:10,deadline:event.startsAt,importance:importance),
    ];
    final plan=engine.buildDay(
      now:now,
      windows:[AvailabilityWindow(id:'emergency',startsAt:now,endsAt:now.add(Duration(minutes:budgetMinutes)),energy:EnergyLevel.high)],
      states:{state.courseId:AdaptiveCourseState(courseId:state.courseId,readiness:state.readiness,openErrors:state.openErrors,dueFlashcards:state.dueFlashcards)},
      tasks:tasks,
      constraints:const AdvancedPlanningConstraints(maxContinuousMinutes:50,breakMinutes:5,maxCoursesPerDay:1,maxCourseSwitches:0,targetReadiness:90),
    );
    await adaptiveRepository.replaceTodayBlocks(plan.blocks,now,reason:'emergency:${event.id}');
    return plan;
  }

  AssessmentImportance _importance(AcademicEventKind? kind)=>switch(kind){
    AcademicEventKind.exam=>AssessmentImportance.high,
    AcademicEventKind.interrogation=>AssessmentImportance.normal,
    AcademicEventKind.assignment=>AssessmentImportance.normal,
    AcademicEventKind.practical=>AssessmentImportance.normal,
    _=>AssessmentImportance.low,
  };

  List<AvailabilityWindow> _todayWindows(DateTime now,List<AvailabilityRule> rules){
    final dayStart=DateTime(now.year,now.month,now.day);
    return [for(final r in rules.where((r)=>r.weekday==now.weekday&&r.isActive)) AvailabilityWindow(
      id:r.id,startsAt:dayStart.add(Duration(minutes:r.startMinute)),endsAt:dayStart.add(Duration(minutes:r.endMinute)),energy:r.energy,
    )];
  }

  List<AvailabilityWindow> _subtractTimetable(DateTime now,List<AvailabilityWindow> source,List<TimetableEntry> timetable){
    final dayStart=DateTime(now.year,now.month,now.day);
    var windows=[...source];
    for(final item in timetable.where((e)=>e.weekday==now.weekday)){
      final busyStart=dayStart.add(Duration(minutes:item.startMinute));
      final busyEnd=dayStart.add(Duration(minutes:item.endMinute));
      final next=<AvailabilityWindow>[];
      for(final w in windows){
        if(!busyStart.isBefore(w.endsAt)||!w.startsAt.isBefore(busyEnd)){next.add(w);continue;}
        if(w.startsAt.isBefore(busyStart)&&busyStart.difference(w.startsAt).inMinutes>=10){next.add(AvailabilityWindow(id:'${w.id}:a',startsAt:w.startsAt,endsAt:busyStart,energy:w.energy));}
        if(busyEnd.isBefore(w.endsAt)&&w.endsAt.difference(busyEnd).inMinutes>=10){next.add(AvailabilityWindow(id:'${w.id}:b',startsAt:busyEnd,endsAt:w.endsAt,energy:w.energy));}
      }
      windows=next;
    }
    return windows;
  }

  List<AvailabilityWindow> _capWindows(List<AvailabilityWindow> source,int minutes){
    var remaining=minutes;
    final result=<AvailabilityWindow>[];
    for(final w in source){
      if(remaining<5) break;
      final available=w.endsAt.difference(w.startsAt).inMinutes;
      final take=available<remaining?available:remaining;
      if(take>=5) result.add(AvailabilityWindow(id:w.id,startsAt:w.startsAt,endsAt:w.startsAt.add(Duration(minutes:take)),energy:w.energy));
      remaining-=take;
    }
    return result;
  }
}

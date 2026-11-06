import '../domain/study_plan.dart';

class GenerateTodayPlan {
  const GenerateTodayPlan(this.repository, {this.engine = const PlanningEngine()});
  final StudyPlanRepository repository;
  final PlanningEngine engine;

  Future<List<StudyPlanItem>> call({required DateTime now, required int budgetMinutes}) async {
    final snapshots = await repository.loadSnapshots();
    final events = await repository.watchUpcomingEvents().first;
    final tomorrow = await repository.loadTomorrowCourseIds(now);
    final plan = engine.build(now: now, budgetMinutes: budgetMinutes, snapshots: snapshots, events: events, tomorrowCourseIds: tomorrow);
    await repository.replaceTodayPlan(plan, now);
    return plan;
  }
}

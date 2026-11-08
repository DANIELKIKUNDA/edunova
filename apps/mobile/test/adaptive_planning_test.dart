import 'package:flutter_test/flutter_test.dart';
import 'package:edunova/src/features/study_plan/domain/adaptive_planning.dart';
import 'package:edunova/src/features/study_plan/domain/study_plan.dart';

void main() {
  final now = DateTime(2026, 9, 20, 8);

  test('high cognitive work is skipped in low energy window', () {
    final plan = const AdaptivePlanningEngine().buildDay(
      now: now,
      windows: [AvailabilityWindow(id: 'w', startsAt: now, endsAt: DateTime(2026,9,20,9), energy: EnergyLevel.low)],
      states: const {'c': AdaptiveCourseState(courseId: 'c', readiness: 20)},
      tasks: const [AdaptiveStudyTask(id: 'hard', courseId: 'c', title: 'Hard', kind: StudyTaskKind.quiz, remainingMinutes: 30, cognitiveLoad: 5)],
    );
    expect(plan.blocks, isEmpty);
  });

  test('planner respects study capacity and breaks', () {
    final plan = const AdaptivePlanningEngine().buildDay(
      now: now,
      windows: [AvailabilityWindow(id: 'w', startsAt: now, endsAt: DateTime(2026,9,20,10), energy: EnergyLevel.high)],
      states: const {'c': AdaptiveCourseState(courseId: 'c', readiness: 20)},
      tasks: const [AdaptiveStudyTask(id: 'long', courseId: 'c', title: 'Long', kind: StudyTaskKind.read, remainingMinutes: 90, maxChunkMinutes: 25)],
      constraints: const AdvancedPlanningConstraints(maxBlockMinutes: 25, maxContinuousMinutes: 25, breakMinutes: 10),
    );
    expect(plan.studyMinutes + plan.breakMinutes <= plan.availableMinutes, isTrue);
    expect(plan.breakMinutes, greaterThan(0));
  });

  test('deferred work gains explicit priority reason', () {
    final plan = const AdaptivePlanningEngine().buildDay(
      now: now,
      windows: [AvailabilityWindow(id: 'w', startsAt: now, endsAt: DateTime(2026,9,20,9), energy: EnergyLevel.medium)],
      states: const {'c': AdaptiveCourseState(courseId: 'c', readiness: 60)},
      tasks: const [AdaptiveStudyTask(id: 'deferred', courseId: 'c', title: 'Deferred', kind: StudyTaskKind.read, remainingMinutes: 20, deferredCount: 2)],
    );
    expect(plan.blocks.first.reasons.any((r) => r.contains('reportée 2 fois')), isTrue);
  });
}

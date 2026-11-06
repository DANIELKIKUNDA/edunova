import 'dart:math' as math;

import 'study_plan.dart';

enum EnergyLevel { low, medium, high }
enum AssessmentImportance { low, normal, high, critical }

class AvailabilityWindow {
  const AvailabilityWindow({
    required this.id,
    required this.startsAt,
    required this.endsAt,
    this.energy = EnergyLevel.medium,
  });
  final String id;
  final DateTime startsAt;
  final DateTime endsAt;
  final EnergyLevel energy;

  int get minutes => endsAt.difference(startsAt).inMinutes;
}

class AdvancedPlanningConstraints {
  const AdvancedPlanningConstraints({
    this.minBlockMinutes = 5,
    this.maxBlockMinutes = 45,
    this.maxContinuousMinutes = 50,
    this.breakMinutes = 10,
    this.maxCoursesPerDay = 4,
    this.maxCourseSwitches = 5,
    this.targetReadiness = 80,
  });
  final int minBlockMinutes;
  final int maxBlockMinutes;
  final int maxContinuousMinutes;
  final int breakMinutes;
  final int maxCoursesPerDay;
  final int maxCourseSwitches;
  final int targetReadiness;
}

class AdaptiveCourseState {
  const AdaptiveCourseState({
    required this.courseId,
    required this.readiness,
    this.readinessConfidence = .5,
    this.openErrors = 0,
    this.dueFlashcards = 0,
    this.unreadSections = 0,
    this.overdueMinutes = 0,
    this.recentStudyMinutes = 0,
    this.lastStudiedAt,
  });
  final String courseId;
  final int readiness;
  final double readinessConfidence;
  final int openErrors;
  final int dueFlashcards;
  final int unreadSections;
  final int overdueMinutes;
  final int recentStudyMinutes;
  final DateTime? lastStudiedAt;
}

class AdaptiveStudyTask {
  const AdaptiveStudyTask({
    required this.id,
    required this.courseId,
    required this.title,
    required this.kind,
    required this.remainingMinutes,
    this.learningValue = .5,
    this.cognitiveLoad = 3,
    this.minChunkMinutes = 5,
    this.maxChunkMinutes = 30,
    this.deadline,
    this.importance = AssessmentImportance.normal,
    this.prerequisiteTaskIds = const [],
    this.pinned = false,
    this.deferredCount = 0,
  });
  final String id;
  final String courseId;
  final String title;
  final StudyTaskKind kind;
  final int remainingMinutes;
  final double learningValue;
  final int cognitiveLoad;
  final int minChunkMinutes;
  final int maxChunkMinutes;
  final DateTime? deadline;
  final AssessmentImportance importance;
  final List<String> prerequisiteTaskIds;
  final bool pinned;
  final int deferredCount;

  AdaptiveStudyTask copyWith({int? remainingMinutes, int? deferredCount, bool? pinned}) => AdaptiveStudyTask(
    id: id, courseId: courseId, title: title, kind: kind,
    remainingMinutes: remainingMinutes ?? this.remainingMinutes,
    learningValue: learningValue, cognitiveLoad: cognitiveLoad,
    minChunkMinutes: minChunkMinutes, maxChunkMinutes: maxChunkMinutes,
    deadline: deadline, importance: importance, prerequisiteTaskIds: prerequisiteTaskIds,
    pinned: pinned ?? this.pinned, deferredCount: deferredCount ?? this.deferredCount,
  );
}

class AdaptivePlanBlock {
  const AdaptivePlanBlock({
    required this.id,
    required this.taskId,
    required this.courseId,
    required this.title,
    required this.kind,
    required this.startsAt,
    required this.endsAt,
    required this.minutes,
    required this.priority,
    required this.reasons,
    required this.windowId,
    this.pinned = false,
    this.status = 'planned',
  });
  final String id;
  final String taskId;
  final String courseId;
  final String title;
  final StudyTaskKind kind;
  final DateTime startsAt;
  final DateTime endsAt;
  final int minutes;
  final int priority;
  final List<String> reasons;
  final String windowId;
  final bool pinned;
  final String status;
}

class AdaptiveDayPlan {
  const AdaptiveDayPlan({
    required this.generatedAt,
    required this.blocks,
    required this.availableMinutes,
    required this.studyMinutes,
    required this.breakMinutes,
    this.warnings = const [],
  });
  final DateTime generatedAt;
  final List<AdaptivePlanBlock> blocks;
  final int availableMinutes;
  final int studyMinutes;
  final int breakMinutes;
  final List<String> warnings;
  double get utilization => availableMinutes <= 0 ? 0 : math.min(1.0, studyMinutes / availableMinutes).toDouble();
}

class _RankedTask {
  const _RankedTask(this.task, this.score, this.reasons);
  final AdaptiveStudyTask task;
  final int score;
  final List<String> reasons;
}

class AdaptivePlanningEngine {
  const AdaptivePlanningEngine();

  double _importance(AssessmentImportance value) => switch (value) {
    AssessmentImportance.low => .75,
    AssessmentImportance.normal => 1,
    AssessmentImportance.high => 1.2,
    AssessmentImportance.critical => 1.4,
  };

  List<_RankedTask> _rank({
    required DateTime now,
    required Map<String, AdaptiveCourseState> states,
    required List<AdaptiveStudyTask> tasks,
    required int targetReadiness,
    required Set<String> completedTaskIds,
  }) {
    final result = <_RankedTask>[];
    for (final task in tasks) {
      if (task.prerequisiteTaskIds.any((id) => !completedTaskIds.contains(id))) continue;
      final state = states[task.courseId] ?? AdaptiveCourseState(courseId: task.courseId, readiness: 0);
      var score = (task.learningValue * 18).round();
      final reasons = <String>[];
      if (task.pinned) { score += 100; reasons.add('tâche épinglée par l’étudiant'); }
      final deadline = task.deadline;
      if (deadline != null) {
        final hours = deadline.difference(now).inMinutes / 60;
        if (hours < 0) { score += 45; reasons.add('tâche en retard'); }
        else if (hours <= 24) { score += (38 * _importance(task.importance)).round(); reasons.add('échéance dans ≤24 h'); }
        else if (hours <= 72) { score += (30 * _importance(task.importance)).round(); reasons.add('échéance dans ≤3 jours'); }
        else if (hours <= 168) { score += (20 * _importance(task.importance)).round(); reasons.add('échéance dans ≤7 jours'); }
        else if (hours <= 336) { score += (10 * _importance(task.importance)).round(); reasons.add('échéance dans ≤14 jours'); }
      }
      final gap = math.max(0, targetReadiness - state.readiness).toInt();
      score += (gap * .35).round();
      if (state.readiness < targetReadiness) reasons.add('préparation sous l’objectif (${state.readiness}/$targetReadiness)');
      if (state.readinessConfidence < .45 && {StudyTaskKind.quiz, StudyTaskKind.diagnostic, StudyTaskKind.mockExam}.contains(task.kind)) {
        score += 8; reasons.add('niveau de maîtrise encore peu fiable');
      }
      if (state.openErrors > 0 && task.kind == StudyTaskKind.errors) { score += math.min(20, state.openErrors * 2).toInt(); reasons.add('${state.openErrors} erreur(s) ouvertes'); }
      if (state.dueFlashcards > 0 && task.kind == StudyTaskKind.flashcards) { score += math.min(14, ((state.dueFlashcards + 1) ~/ 2)).toInt(); reasons.add('${state.dueFlashcards} flashcard(s) dues'); }
      if (state.unreadSections > 0 && {StudyTaskKind.read, StudyTaskKind.summary}.contains(task.kind)) { score += math.min(12, state.unreadSections).toInt(); reasons.add('sections du cours non couvertes'); }
      if (state.overdueMinutes > 0) { score += math.min(15, ((state.overdueMinutes + 9) ~/ 10)).toInt(); reasons.add('retard de révision à résorber'); }
      if (task.deferredCount > 0) { score += math.min(15, task.deferredCount * 4).toInt(); reasons.add('reportée ${task.deferredCount} fois'); }
      if (state.recentStudyMinutes >= 120 && !{StudyTaskKind.errors, StudyTaskKind.flashcards}.contains(task.kind)) { score -= 8; reasons.add('matière déjà fortement travaillée récemment'); }
      result.add(_RankedTask(task, score.clamp(0, 200).toInt(), reasons.toSet().toList()));
    }
    result.sort((a, b) {
      final byScore = b.score.compareTo(a.score);
      if (byScore != 0) return byScore;
      final ad = a.task.deadline;
      final bd = b.task.deadline;
      if (ad != null && bd != null) return ad.compareTo(bd);
      if (ad != null) return -1;
      if (bd != null) return 1;
      return a.task.id.compareTo(b.task.id);
    });
    return result;
  }

  AdaptiveDayPlan buildDay({
    required DateTime now,
    required List<AvailabilityWindow> windows,
    required Map<String, AdaptiveCourseState> states,
    required List<AdaptiveStudyTask> tasks,
    AdvancedPlanningConstraints constraints = const AdvancedPlanningConstraints(),
    Set<String> completedTaskIds = const {},
  }) {
    final sortedWindows = windows.where((w) => w.endsAt.isAfter(now)).toList()..sort((a,b) => a.startsAt.compareTo(b.startsAt));
    final ranked = _rank(now: now, states: states, tasks: tasks, targetReadiness: constraints.targetReadiness, completedTaskIds: completedTaskIds);
    final remaining = {for (final row in ranked) row.task.id: row.task.remainingMinutes};
    final completed = {...completedTaskIds};
    final blocks = <AdaptivePlanBlock>[];
    final coursesUsed = <String>[];
    var switches = 0;
    String? lastCourse;
    var breakTotal = 0;
    final warnings = <String>[];

    for (final window in sortedWindows) {
      var cursor = window.startsAt.isBefore(now) ? now : window.startsAt;
      var continuous = 0;
      while (cursor.isBefore(window.endsAt)) {
        final available = window.endsAt.difference(cursor).inMinutes;
        if (available < constraints.minBlockMinutes) break;
        final eligible = <(_RankedTask, int)>[];
        for (final row in ranked) {
          final task = row.task;
          if ((remaining[task.id] ?? 0) <= 0) continue;
          if (task.prerequisiteTaskIds.any((id) => !completed.contains(id))) continue;
          if (!coursesUsed.contains(task.courseId) && coursesUsed.toSet().length >= constraints.maxCoursesPerDay) continue;
          if (lastCourse != null && task.courseId != lastCourse && switches >= constraints.maxCourseSwitches) continue;
          if (window.energy == EnergyLevel.low && task.cognitiveLoad >= 4) continue;
          var bonus = 0;
          if (window.energy == EnergyLevel.high && task.cognitiveLoad >= 4) bonus += 8;
          if (window.energy == EnergyLevel.low && task.cognitiveLoad <= 2) bonus += 5;
          if (lastCourse == task.courseId) bonus += 3;
          eligible.add((row, row.score + bonus));
        }
        if (eligible.isEmpty) break;
        eligible.sort((a,b) => b.$2.compareTo(a.$2));
        final selected = eligible.first.$1;
        final task = selected.task;
        final maxChunk = [
          task.maxChunkMinutes,
          constraints.maxBlockMinutes,
          constraints.maxContinuousMinutes - continuous,
          available,
          remaining[task.id]!,
        ].reduce((a,b)=>a<b?a:b);
        if (maxChunk < task.minChunkMinutes) {
          if (continuous >= constraints.maxContinuousMinutes - constraints.minBlockMinutes && constraints.breakMinutes > 0) {
            final shifted = cursor.add(Duration(minutes: constraints.breakMinutes));
            if (shifted.isBefore(window.endsAt)) {
              cursor = shifted; breakTotal += constraints.breakMinutes; continuous = 0; continue;
            }
          }
          break;
        }
        final end = cursor.add(Duration(minutes: maxChunk));
        blocks.add(AdaptivePlanBlock(
          id: '${cursor.year}-${cursor.month}-${cursor.day}:${task.id}:${blocks.length + 1}',
          taskId: task.id, courseId: task.courseId, title: task.title, kind: task.kind,
          startsAt: cursor, endsAt: end, minutes: maxChunk, priority: selected.score,
          reasons: selected.reasons, windowId: window.id, pinned: task.pinned,
        ));
        remaining[task.id] = remaining[task.id]! - maxChunk;
        if (remaining[task.id]! <= 0) completed.add(task.id);
        if (lastCourse != null && lastCourse != task.courseId) switches++;
        lastCourse = task.courseId;
        coursesUsed.add(task.courseId);
        cursor = end;
        continuous += maxChunk;
        if (continuous >= constraints.maxContinuousMinutes && constraints.breakMinutes > 0) {
          final shifted = cursor.add(Duration(minutes: constraints.breakMinutes));
          if (!shifted.isAfter(window.endsAt)) { cursor = shifted; breakTotal += constraints.breakMinutes; }
          continuous = 0;
        }
      }
    }
    final availableMinutes = sortedWindows.fold<int>(0, (sum, w) {
      final start = w.startsAt.isBefore(now) ? now : w.startsAt;
      return sum + math.max(0, w.endsAt.difference(start).inMinutes).toInt();
    });
    final studyMinutes = blocks.fold<int>(0, (sum, b) => sum + b.minutes);
    if (sortedWindows.isEmpty) warnings.add('aucune plage d’étude disponible');
    if (remaining.values.fold<int>(0,(a,b)=>a+b) > 0 && availableMinutes > 0 && studyMinutes >= (availableMinutes * .85)) {
      warnings.add('charge supérieure à la capacité disponible aujourd’hui');
    }
    return AdaptiveDayPlan(generatedAt: now, blocks: blocks, availableMinutes: availableMinutes, studyMinutes: studyMinutes, breakMinutes: breakTotal, warnings: warnings);
  }
}

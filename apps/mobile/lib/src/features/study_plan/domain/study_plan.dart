enum AcademicEventKind { course, interrogation, exam, assignment, practical, personal }
enum StudyTaskKind { read, summary, flashcards, quiz, errors, mockExam, diagnostic }

class TimetableEntry {
  const TimetableEntry({required this.id, required this.title, required this.weekday, required this.startMinute, required this.endMinute, this.courseId, this.location});
  final String id;
  final String? courseId;
  final String title;
  final int weekday;
  final int startMinute;
  final int endMinute;
  final String? location;
}

class AcademicEvent {
  const AcademicEvent({required this.id, required this.title, required this.kind, required this.startsAt, this.courseId, this.endsAt, this.notes});
  final String id;
  final String? courseId;
  final String title;
  final AcademicEventKind kind;
  final DateTime startsAt;
  final DateTime? endsAt;
  final String? notes;
}

class CoursePlanningSnapshot {
  const CoursePlanningSnapshot({required this.courseId, required this.title, required this.readiness, this.openErrors = 0, this.dueFlashcards = 0, this.hasQuiz = false, this.hasSummary = false});
  final String courseId;
  final String title;
  final int readiness;
  final int openErrors;
  final int dueFlashcards;
  final bool hasQuiz;
  final bool hasSummary;
}

class StudyTaskCandidate {
  const StudyTaskCandidate({required this.id, required this.courseId, required this.title, required this.kind, required this.minutes, this.learningValue = .5, this.splittable = true});
  final String id;
  final String courseId;
  final String title;
  final StudyTaskKind kind;
  final int minutes;
  final double learningValue;
  final bool splittable;
}

class StudyPlanItem {
  const StudyPlanItem({required this.id, required this.courseId, required this.title, required this.kind, required this.minutes, required this.priority, required this.reasons, this.status = 'pending'});
  final String id;
  final String courseId;
  final String title;
  final StudyTaskKind kind;
  final int minutes;
  final int priority;
  final List<String> reasons;
  final String status;
}

class PlanningEngine {
  const PlanningEngine();

  List<StudyPlanItem> build({
    required DateTime now,
    required int budgetMinutes,
    required List<CoursePlanningSnapshot> snapshots,
    required List<AcademicEvent> events,
    required Set<String> tomorrowCourseIds,
  }) {
    final candidates = <StudyTaskCandidate>[];
    for (final state in snapshots) {
      if (state.openErrors > 0) {
        candidates.add(StudyTaskCandidate(id: 'errors:${state.courseId}', courseId: state.courseId, title: 'Revoir mes erreurs · ${state.title}', kind: StudyTaskKind.errors, minutes: 10, learningValue: 1));
      }
      if (state.dueFlashcards > 0) {
        candidates.add(StudyTaskCandidate(id: 'flash:${state.courseId}', courseId: state.courseId, title: 'Flashcards · ${state.title}', kind: StudyTaskKind.flashcards, minutes: 8, learningValue: .85));
      }
      if (state.hasQuiz) {
        candidates.add(StudyTaskCandidate(id: 'quiz:${state.courseId}', courseId: state.courseId, title: 'Quiz ciblé · ${state.title}', kind: StudyTaskKind.quiz, minutes: 15, learningValue: .9));
      }
      if (state.hasSummary) {
        candidates.add(StudyTaskCandidate(id: 'summary:${state.courseId}', courseId: state.courseId, title: 'Résumé · ${state.title}', kind: StudyTaskKind.summary, minutes: 10, learningValue: .7));
      }
      candidates.add(StudyTaskCandidate(id: 'read:${state.courseId}', courseId: state.courseId, title: 'Continuer ${state.title}', kind: StudyTaskKind.read, minutes: 20, learningValue: .6));
    }

    final byCourse = {for (final row in snapshots) row.courseId: row};
    final nearest = <String, AcademicEvent>{};
    for (final event in events.where((e) => e.courseId != null && e.startsAt.isAfter(now))) {
      final current = nearest[event.courseId!];
      if (current == null || event.startsAt.isBefore(current.startsAt)) nearest[event.courseId!] = event;
    }

    final ranked = <StudyPlanItem>[];
    for (final task in candidates) {
      final state = byCourse[task.courseId];
      if (state == null) continue;
      var score = (task.learningValue * 20).round();
      final reasons = <String>[];
      final event = nearest[task.courseId];
      if (event != null) {
        final hours = event.startsAt.difference(now).inMinutes / 60;
        if (hours <= 24) { score += 40; reasons.add('évaluation dans ≤24 h'); }
        else if (hours <= 72) { score += 30; reasons.add('évaluation dans ≤3 jours'); }
        else if (hours <= 168) { score += 20; reasons.add('évaluation dans ≤7 jours'); }
        else if (hours <= 336) { score += 10; reasons.add('évaluation dans ≤14 jours'); }
      }
      score += ((100 - state.readiness) * .25).round();
      if (state.readiness < 50) reasons.add('préparation faible');
      if (state.openErrors > 0) { score += (state.openErrors * 2).clamp(0, 18).toInt(); reasons.add('${state.openErrors} erreur(s) à corriger'); }
      if (state.dueFlashcards > 0) { score += ((state.dueFlashcards + 2) ~/ 3).clamp(0, 10).toInt(); reasons.add('flashcards dues'); }
      if (tomorrowCourseIds.contains(task.courseId)) { score += 8; reasons.add('cours prévu demain'); }
      ranked.add(StudyPlanItem(id: task.id, courseId: task.courseId, title: task.title, kind: task.kind, minutes: task.minutes, priority: score.clamp(0, 100).toInt(), reasons: reasons));
    }
    ranked.sort((a,b) => b.priority != a.priority ? b.priority.compareTo(a.priority) : a.minutes.compareTo(b.minutes));

    var remaining = budgetMinutes;
    final selected = <StudyPlanItem>[];
    for (final row in ranked) {
      if (remaining < 5) break;
      final minutes = row.minutes <= remaining ? row.minutes : remaining;
      if (minutes < 5) continue;
      selected.add(StudyPlanItem(id: row.id, courseId: row.courseId, title: row.title, kind: row.kind, minutes: minutes, priority: row.priority, reasons: row.reasons));
      remaining -= minutes;
    }
    return selected;
  }

  List<StudyPlanItem> emergency({required AcademicEvent event, required CoursePlanningSnapshot state, int budgetMinutes = 60}) {
    final specs = <(StudyTaskKind,String,double)>[
      (StudyTaskKind.diagnostic,'Diagnostic rapide',.18),
      (StudyTaskKind.summary,'Points essentiels',.24),
      (StudyTaskKind.errors,'Revoir mes erreurs',state.openErrors > 0 ? .24 : .12),
      (StudyTaskKind.quiz,'Quiz ciblé',.18),
      (StudyTaskKind.mockExam,'Mini examen blanc',.16),
    ];
    var allocated = 0;
    return [for (var i=0;i<specs.length;i++) () {
      final spec = specs[i];
      final minutes = i == specs.length - 1 ? budgetMinutes - allocated : (budgetMinutes * spec.$3).round().clamp(5, budgetMinutes).toInt();
      allocated += minutes;
      return StudyPlanItem(id:'emergency:${event.id}:${spec.$1.name}',courseId:state.courseId,title:spec.$2,kind:spec.$1,minutes:minutes,priority:100-i,reasons:const ['évaluation imminente']);
    }()];
  }
}

abstract interface class StudyPlanRepository {
  Stream<List<StudyPlanItem>> watchTodayPlan();
  Stream<List<AcademicEvent>> watchUpcomingEvents();
  Stream<List<TimetableEntry>> watchTimetable();
  Future<List<CoursePlanningSnapshot>> loadSnapshots();
  Future<Set<String>> loadTomorrowCourseIds(DateTime now);
  Future<void> replaceTodayPlan(List<StudyPlanItem> items, DateTime generatedAt);
  Future<void> markCompleted(String id);
  Future<void> saveEvent(AcademicEvent event);
  Future<List<TimetableEntry>> findTimetableConflicts(TimetableEntry candidate);
  Future<void> saveTimetableEntry(TimetableEntry entry);
}

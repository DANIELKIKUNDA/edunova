import '../../../core/security/local_account_access.dart';
import 'dart:convert';
import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';
import '../../../core/database/app_database.dart';
import '../../sync/infrastructure/cloud_mutation_writer.dart';
import '../domain/study_plan.dart';

class DriftStudyPlanRepository implements StudyPlanRepository {
  final LocalAccountAccess _access = LocalAccountAccess();
  DriftStudyPlanRepository(this.db,{required this.accountIdProvider});
  final AppDatabase db;
  final Future<String?> Function() accountIdProvider;
  static const _uuid = Uuid();

  Future<void> _outbox(String aggregateType,String aggregateId,String eventType,Map<String,Object?> payload) async {
    await _access.assertOwned();
    await db.into(db.localOutboxItems).insert(LocalOutboxItemsCompanion.insert(
      id:_uuid.v4(),aggregateType:aggregateType,aggregateId:aggregateId,eventType:eventType,payloadJson:jsonEncode(payload),occurredAt:DateTime.now().toUtc(),
    ));
  }
  String _dayKey(DateTime d) => '${d.year.toString().padLeft(4,'0')}-${d.month.toString().padLeft(2,'0')}-${d.day.toString().padLeft(2,'0')}';

  @override
  Stream<List<StudyPlanItem>> watchTodayPlan() {
    final key = _dayKey(DateTime.now());
    final q = db.select(db.localStudyPlanTasks)..where((t)=>t.dayKey.equals(key))..orderBy([(t)=>OrderingTerm.desc(t.priority)]);
    return _access.protect(q.watch().map((rows)=>rows.map((r)=>StudyPlanItem(id:r.id,courseId:r.courseId,title:r.title,kind:StudyTaskKind.values.byName(r.kind),minutes:r.minutes,priority:r.priority,reasons:((jsonDecode(r.reasonsJson) as List).cast<String>()),status:r.status)).toList()));
  }

  @override
  Stream<List<AcademicEvent>> watchUpcomingEvents() {
    final q = db.select(db.localAcademicEvents)..where((t)=>t.isActive.equals(true) & t.startsAt.isBiggerOrEqualValue(DateTime.now()))..orderBy([(t)=>OrderingTerm.asc(t.startsAt)]);
    return _access.protect(q.watch().map((rows)=>rows.map((r)=>AcademicEvent(id:r.id,courseId:r.courseId,title:r.title,kind:AcademicEventKind.values.byName(r.kind),startsAt:r.startsAt,endsAt:r.endsAt,notes:r.notes)).toList()));
  }

  @override
  Stream<List<TimetableEntry>> watchTimetable() {
    final q = db.select(db.localTimetableEntries)..orderBy([(t)=>OrderingTerm.asc(t.weekday),(t)=>OrderingTerm.asc(t.startMinute)]);
    return _access.protect(q.watch().map((rows)=>rows.map((r)=>TimetableEntry(id:r.id,courseId:r.courseId,title:r.title,weekday:r.weekday,startMinute:r.startMinute,endMinute:r.endMinute,location:r.location)).toList()));
  }

  @override
  Future<List<CoursePlanningSnapshot>> loadSnapshots() async {
    await _access.assertOwned();
    final courses = await db.select(db.localCourseRecords).get();
    final errors = await db.select(db.localErrorLedgerItems).get();
    final cards = db.localFlashcards;
    final states = db.localFlashcardStates;
    final dueRows = await (db.select(cards).join([leftOuterJoin(states,states.flashcardId.equalsExp(cards.id))])..where(states.dueAt.isNull() | states.dueAt.isSmallerOrEqualValue(DateTime.now()))).get();
    final questions = await db.select(db.localQuizQuestions).get();
    final summaries = await db.select(db.localSummaries).get();
    return courses.map((c) {
      final openErrors = errors.where((e)=>e.courseId==c.id && e.recoveredAt==null).length;
      final due = dueRows.where((row)=>row.readTable(cards).courseId==c.id).length;
      return CoursePlanningSnapshot(courseId:c.id,title:c.title,readiness:(c.progress.clamp(0,1)*100).round(),openErrors:openErrors,dueFlashcards:due,hasQuiz:questions.any((q)=>q.courseId==c.id),hasSummary:summaries.any((s)=>s.courseId==c.id));
    }).toList();
  }

  @override
  Future<Set<String>> loadTomorrowCourseIds(DateTime now) async {
    await _access.assertOwned();
    final tomorrowWeekday = now.add(const Duration(days:1)).weekday;
    final rows = await (db.select(db.localTimetableEntries)..where((t)=>t.weekday.equals(tomorrowWeekday))).get();
    return rows.map((e)=>e.courseId).whereType<String>().toSet();
  }

  @override
  Future<void> replaceTodayPlan(List<StudyPlanItem> items, DateTime generatedAt) async {
    await _access.assertOwned();
    final key = _dayKey(generatedAt);
    await db.transaction(() async {
      await (db.delete(db.localStudyPlanTasks)..where((t)=>t.dayKey.equals(key) & t.status.equals('pending'))).go();
      for (final item in items) {
        await db.into(db.localStudyPlanTasks).insertOnConflictUpdate(LocalStudyPlanTasksCompanion.insert(
          id:'$key:${item.id}',dayKey:key,courseId:item.courseId,title:item.title,kind:item.kind.name,minutes:item.minutes,priority:item.priority,
          reasonsJson:Value(jsonEncode(item.reasons)),generatedAt:generatedAt,updatedAt:generatedAt,
        ));
      }
    });
  }

  @override
  Future<void> markCompleted(String id) async {
    await _access.assertOwned();
    await (db.update(db.localStudyPlanTasks)..where((t)=>t.id.equals(id))).write(LocalStudyPlanTasksCompanion(status:const Value('completed'),updatedAt:Value(DateTime.now())));
  }

  @override
  Future<void> saveEvent(AcademicEvent event) async {
    await _access.assertOwned();
    final now=DateTime.now();
    await db.transaction(() async {
      await db.into(db.localAcademicEvents).insertOnConflictUpdate(LocalAcademicEventsCompanion.insert(
        id:event.id,courseId:Value(event.courseId),title:event.title,kind:event.kind.name,startsAt:event.startsAt,endsAt:Value(event.endsAt),notes:Value(event.notes),updatedAt:now,
      ));
      await (db.delete(db.localNotificationIntents)..where((t)=>t.eventId.equals(event.id))).go();
      final offsets=<String,Duration>{'j-3':const Duration(days:3),'j-1':const Duration(days:1),'h-3':const Duration(hours:3)};
      for(final item in offsets.entries){
        final fireAt=event.startsAt.subtract(item.value);
        if(!fireAt.isAfter(now)) continue;
        await db.into(db.localNotificationIntents).insert(LocalNotificationIntentsCompanion.insert(
          id:_uuid.v4(), eventId:event.id, dedupeKey:Value('assessment:${event.id}:${item.key}'),
          fireAt:fireAt, expiresAt:Value(event.startsAt), title:event.title,
          body:'${event.title} approche. Ouvre EduNova pour vérifier ta préparation.', category:'assessment',
          deepLink:Value('/calendar?event=${event.id}'), priority:Value(item.key=='h-3'?96:item.key=='j-1'?86:72),
        ));
      }
      final payload={'title':event.title,'kind':event.kind.name,'startsAt':event.startsAt.toUtc().toIso8601String(),'endsAt':event.endsAt?.toUtc().toIso8601String(),'courseId':event.courseId,'notes':event.notes};
      await _outbox('academicEvent',event.id,'planning.event.saved',payload);
      await CloudMutationWriter(db:db,accountIdProvider:accountIdProvider).upsert('calendar_event',event.id,payload,now);
    });
  }

  @override
  Future<List<TimetableEntry>> findTimetableConflicts(TimetableEntry candidate) async {
    await _access.assertOwned();
    final rows=await (db.select(db.localTimetableEntries)..where((t)=>t.weekday.equals(candidate.weekday) & t.id.equals(candidate.id).not())).get();
    return rows.where((r)=>candidate.startMinute<r.endMinute && r.startMinute<candidate.endMinute).map((r)=>TimetableEntry(id:r.id,courseId:r.courseId,title:r.title,weekday:r.weekday,startMinute:r.startMinute,endMinute:r.endMinute,location:r.location)).toList();
  }

  @override
  Future<void> saveTimetableEntry(TimetableEntry entry) async {
    await _access.assertOwned();
    await db.transaction(() async {
      await db.into(db.localTimetableEntries).insertOnConflictUpdate(LocalTimetableEntriesCompanion.insert(
        id:entry.id,courseId:Value(entry.courseId),title:entry.title,weekday:entry.weekday,startMinute:entry.startMinute,endMinute:entry.endMinute,location:Value(entry.location),updatedAt:DateTime.now(),
      ));
      final payload={'title':entry.title,'weekday':entry.weekday,'startMinute':entry.startMinute,'endMinute':entry.endMinute,'courseId':entry.courseId,'location':entry.location};
      await _outbox('timetableEntry',entry.id,'planning.timetable.saved',payload);
      await CloudMutationWriter(db:db,accountIdProvider:accountIdProvider).upsert('timetable_entry',entry.id,payload,DateTime.now().toUtc());
    });
  }
}

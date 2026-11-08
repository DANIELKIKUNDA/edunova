import '../../../core/security/local_account_access.dart';
import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';

import '../../../core/database/app_database.dart';
import '../../sync/infrastructure/cloud_mutation_writer.dart';
import '../application/adaptive_planning_repository.dart';
import '../domain/adaptive_planning.dart';
import '../domain/study_plan.dart';

class DriftAdaptivePlanningRepository implements AdaptivePlanningRepository {
  final LocalAccountAccess _access = LocalAccountAccess();
  DriftAdaptivePlanningRepository(this.db,{required this.accountIdProvider});
  final AppDatabase db;
  final Future<String?> Function() accountIdProvider;
  static const _uuid = Uuid();

  String _dayKey(DateTime d) => '${d.year.toString().padLeft(4,'0')}-${d.month.toString().padLeft(2,'0')}-${d.day.toString().padLeft(2,'0')}';

  Future<void> _outbox(String aggregateType,String aggregateId,String eventType,Map<String,Object?> payload) async {
    await _access.assertOwned();
    await db.into(db.localOutboxItems).insert(LocalOutboxItemsCompanion.insert(
      id:_uuid.v4(),aggregateType:aggregateType,aggregateId:aggregateId,eventType:eventType,
      payloadJson:jsonEncode(payload),occurredAt:DateTime.now().toUtc(),
    ));
  }

  @override
  Stream<List<AvailabilityRule>> watchAvailabilityRules() {
    final q=db.select(db.localStudyAvailabilityRules)..where((t)=>t.isActive.equals(true))..orderBy([(t)=>OrderingTerm.asc(t.weekday),(t)=>OrderingTerm.asc(t.startMinute)]);
    return _access.protect(q.watch().map((rows)=>rows.map((r)=>AvailabilityRule(
      id:r.id,weekday:r.weekday,startMinute:r.startMinute,endMinute:r.endMinute,
      energy:EnergyLevel.values.byName(r.energy),isActive:r.isActive,
    )).toList()));
  }

  @override
  Stream<List<AdaptivePlanBlock>> watchTodayBlocks() {
    final now=DateTime.now();
    final start=DateTime(now.year,now.month,now.day);
    final end=start.add(const Duration(days:1));
    final q=db.select(db.localAdaptiveStudyBlocks)
      ..where((t)=>t.startsAt.isBiggerOrEqualValue(start) & t.startsAt.isSmallerThanValue(end))
      ..orderBy([(t)=>OrderingTerm.asc(t.startsAt)]);
    return _access.protect(q.watch().map((rows)=>rows.map((r)=>AdaptivePlanBlock(
      id:r.id,taskId:r.taskId,courseId:r.courseId,title:r.title,kind:StudyTaskKind.values.byName(r.kind),
      startsAt:r.startsAt,endsAt:r.endsAt,minutes:r.endsAt.difference(r.startsAt).inMinutes,
      priority:r.priority,reasons:(jsonDecode(r.reasonsJson) as List).cast<String>(),windowId:'local',pinned:r.pinned,status:r.status,
    )).toList()));
  }

  @override
  Future<Map<String, PlanningDebt>> loadDebts() async {
    await _access.assertOwned();
    final rows=await db.select(db.localPlanningDebts).get();
    return {for(final r in rows) r.courseId:PlanningDebt(courseId:r.courseId,overdueMinutes:r.overdueMinutes,deferredCount:r.deferredCount)};
  }

  @override
  Future<PlanningPreferences> loadPreferences() async {
    await _access.assertOwned();
    final row=await (db.select(db.localPlanningPreferences)..where((t)=>t.id.equals('default'))).getSingleOrNull();
    if(row==null) return const PlanningPreferences();
    return PlanningPreferences(
      dailyBudgetMinutes:row.dailyBudgetMinutes,maxNotificationsPerDay:row.maxNotificationsPerDay,
      quietStartMinute:row.quietStartMinute,quietEndMinute:row.quietEndMinute,
      maxContinuousMinutes:row.maxContinuousMinutes,breakMinutes:row.breakMinutes,
      maxCoursesPerDay:row.maxCoursesPerDay,maxCourseSwitches:row.maxCourseSwitches,
      targetReadiness:row.targetReadiness,planningHorizonDays:row.planningHorizonDays,
    );
  }

  @override
  Future<void> savePreferences(PlanningPreferences value) async {
    await _access.assertOwned();
    final now=DateTime.now();
    await db.into(db.localPlanningPreferences).insertOnConflictUpdate(LocalPlanningPreferencesCompanion.insert(
      dailyBudgetMinutes:Value(value.dailyBudgetMinutes),maxNotificationsPerDay:Value(value.maxNotificationsPerDay),
      quietStartMinute:Value(value.quietStartMinute),quietEndMinute:Value(value.quietEndMinute),
      maxContinuousMinutes:Value(value.maxContinuousMinutes),breakMinutes:Value(value.breakMinutes),
      maxCoursesPerDay:Value(value.maxCoursesPerDay),maxCourseSwitches:Value(value.maxCourseSwitches),
      targetReadiness:Value(value.targetReadiness),planningHorizonDays:Value(value.planningHorizonDays),updatedAt:now,
    ));
    final payload={
      'dailyBudgetMinutes':value.dailyBudgetMinutes,'maxNotificationsPerDay':value.maxNotificationsPerDay,
      'quietStartMinute':value.quietStartMinute,'quietEndMinute':value.quietEndMinute,
      'maxContinuousMinutes':value.maxContinuousMinutes,'breakMinutes':value.breakMinutes,
      'maxCoursesPerDay':value.maxCoursesPerDay,'maxCourseSwitches':value.maxCourseSwitches,
      'targetReadiness':value.targetReadiness,'planningHorizonDays':value.planningHorizonDays,
    };
    await _outbox('planningPreferences','default','planning.preferences.updated',payload);
    await CloudMutationWriter(db:db,accountIdProvider:accountIdProvider).upsert('planning_preferences','default',payload,now.toUtc());
  }

  @override
  Future<void> saveAvailabilityRule(AvailabilityRule value) async {
    await _access.assertOwned();
    await db.into(db.localStudyAvailabilityRules).insertOnConflictUpdate(LocalStudyAvailabilityRulesCompanion.insert(
      id:value.id,weekday:value.weekday,startMinute:value.startMinute,endMinute:value.endMinute,
      energy:Value(value.energy.name),isActive:Value(value.isActive),updatedAt:DateTime.now(),
    ));
    await _outbox('availability',value.id,'planning.availability.saved',{
      'weekday':value.weekday,'startMinute':value.startMinute,'endMinute':value.endMinute,'energy':value.energy.name,
    });
  }

  @override
  Future<void> deleteAvailabilityRule(String id) async {
    await _access.assertOwned();
    await (db.update(db.localStudyAvailabilityRules)..where((t)=>t.id.equals(id))).write(LocalStudyAvailabilityRulesCompanion(isActive:const Value(false),updatedAt:Value(DateTime.now())));
    await _outbox('availability',id,'planning.availability.deleted',{});
  }

  @override
  Future<void> replaceTodayBlocks(List<AdaptivePlanBlock> blocks,DateTime generatedAt,{required String reason}) async {
    final dayKey=_dayKey(generatedAt);
    final revisionId=_uuid.v4();
    final fingerprint=base64Url.encode(utf8.encode(blocks.map((b)=>'${b.taskId}:${b.startsAt.toIso8601String()}:${b.minutes}').join('|')));
    await db.transaction(() async {
      await db.into(db.localPlanRevisions).insert(LocalPlanRevisionsCompanion.insert(id:revisionId,dayKey:dayKey,reason:reason,fingerprint:fingerprint,generatedAt:generatedAt));
      final start=DateTime(generatedAt.year,generatedAt.month,generatedAt.day);
      final end=start.add(const Duration(days:1));
      final protected=await (db.select(db.localAdaptiveStudyBlocks)..where((t)=>t.startsAt.isBiggerOrEqualValue(start) & t.startsAt.isSmallerThanValue(end) & (t.pinned.equals(true) | t.status.equals('completed')))).get();
      final protectedIds=protected.map((e)=>e.id).toSet();
      await (db.delete(db.localAdaptiveStudyBlocks)..where((t)=>t.startsAt.isBiggerOrEqualValue(start) & t.startsAt.isSmallerThanValue(end) & t.status.equals('planned') & t.pinned.equals(false))).go();
      for(final b in blocks){
        if(protectedIds.contains(b.id)) continue;
        await db.into(db.localAdaptiveStudyBlocks).insertOnConflictUpdate(LocalAdaptiveStudyBlocksCompanion.insert(
          id:b.id,revisionId:revisionId,taskId:b.taskId,courseId:b.courseId,title:b.title,kind:b.kind.name,
          startsAt:b.startsAt,endsAt:b.endsAt,priority:b.priority,reasonsJson:Value(jsonEncode(b.reasons)),
          pinned:Value(b.pinned),updatedAt:generatedAt,
        ));
      }
    });
    await _outbox('studyPlan',revisionId,'planning.plan.replaced',{'dayKey':dayKey,'reason':reason,'blockCount':blocks.length,'fingerprint':fingerprint});
  }

  @override
  Future<void> completeBlock(String blockId,{required int actualMinutes}) async {
    final block=await (db.select(db.localAdaptiveStudyBlocks)..where((t)=>t.id.equals(blockId))).getSingle();
    final now=DateTime.now();
    await db.transaction(() async {
      await (db.update(db.localAdaptiveStudyBlocks)..where((t)=>t.id.equals(blockId))).write(LocalAdaptiveStudyBlocksCompanion(status:const Value('completed'),updatedAt:Value(now)));
      await db.into(db.localStudySessions).insert(LocalStudySessionsCompanion.insert(
        id:_uuid.v4(),blockId:Value(blockId),courseId:block.courseId,taskId:Value(block.taskId),startedAt:block.startsAt,
        endedAt:Value(now),plannedMinutes:Value(block.endsAt.difference(block.startsAt).inMinutes),actualMinutes:Value(actualMinutes),outcome:const Value('completed'),updatedAt:now,
      ));
      await db.into(db.localPlanActions).insert(LocalPlanActionsCompanion.insert(id:_uuid.v4(),blockId:blockId,action:'completed',payloadJson:Value(jsonEncode({'actualMinutes':actualMinutes})),occurredAt:now));
    });
    await _outbox('studyBlock',blockId,'planning.block.completed',{'actualMinutes':actualMinutes,'courseId':block.courseId,'taskId':block.taskId});
  }

  @override
  Future<void> deferBlock(String blockId,{int days=1}) async {
    final block=await (db.select(db.localAdaptiveStudyBlocks)..where((t)=>t.id.equals(blockId))).getSingle();
    final now=DateTime.now();
    final existing=await (db.select(db.localPlanningDebts)..where((t)=>t.courseId.equals(block.courseId))).getSingleOrNull();
    final minutes=block.endsAt.difference(block.startsAt).inMinutes;
    await db.transaction(() async {
      await (db.update(db.localAdaptiveStudyBlocks)..where((t)=>t.id.equals(blockId))).write(LocalAdaptiveStudyBlocksCompanion(status:const Value('deferred'),updatedAt:Value(now)));
      await db.into(db.localPlanningDebts).insertOnConflictUpdate(LocalPlanningDebtsCompanion.insert(
        courseId:block.courseId,overdueMinutes:Value((existing?.overdueMinutes ?? 0)+minutes),
        deferredCount:Value((existing?.deferredCount ?? 0)+1),lastDeferredAt:Value(now),updatedAt:now,
      ));
      await db.into(db.localPlanActions).insert(LocalPlanActionsCompanion.insert(id:_uuid.v4(),blockId:blockId,action:'deferred',payloadJson:Value(jsonEncode({'days':days})),occurredAt:now));
    });
    await _outbox('studyBlock',blockId,'planning.block.deferred',{'days':days,'courseId':block.courseId,'minutes':minutes});
  }

  @override
  Future<void> setPinned(String blockId,bool value) async {
    await _access.assertOwned();
    await (db.update(db.localAdaptiveStudyBlocks)..where((t)=>t.id.equals(blockId))).write(LocalAdaptiveStudyBlocksCompanion(pinned:Value(value),updatedAt:Value(DateTime.now())));
    await db.into(db.localPlanActions).insert(LocalPlanActionsCompanion.insert(id:_uuid.v4(),blockId:blockId,action:value?'pinned':'unpinned',occurredAt:DateTime.now()));
  }
}

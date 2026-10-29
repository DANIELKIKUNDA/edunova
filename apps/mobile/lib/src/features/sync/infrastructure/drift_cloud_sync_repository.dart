import 'dart:convert';
import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';
import '../../../core/database/app_database.dart';
import '../application/cloud_sync_repository.dart';
import '../domain/cloud_sync.dart';

class DriftCloudSyncRepository implements CloudSyncLocalRepository {
  DriftCloudSyncRepository(this.db);
  final AppDatabase db;
  static const _uuid = Uuid();

  @override
  Future<CloudSyncState> ensureState(String accountId) async {
    if (accountId.trim().isEmpty) {
      throw StateError('cloud_sync_account_required');
    }
    // The projections (academic profile, calendar, reading progress, etc.) are
    // currently global SQLite tables, NOT account-scoped. Until a schema
    // migration or separate per-account database is implemented, syncing a
    // second account in this installation would expose/overwrite the first
    // account's local data. Fail closed rather than silently mixing accounts.
    // This guard must also run for existing sync states, not only first setup.
    final existingStates = await db.select(db.localCloudSyncStates).get();
    if (existingStates.any((state) => state.id != accountId)) {
      throw StateError('cloud_sync_shared_database_account_switch_unsupported');
    }
    var row = await (db.select(db.localCloudSyncStates)
          ..where((t) => t.id.equals(accountId)))
        .getSingleOrNull();
    if (row == null) {
      final now = DateTime.now().toUtc();
      await db.transaction(() async {
        // Repeat the check within the write transaction to avoid concurrent
        // first-use initializations claiming the same global projections.
        final states = await db.select(db.localCloudSyncStates).get();
        if (states.any((state) => state.id != accountId)) {
          throw StateError('cloud_sync_shared_database_account_switch_unsupported');
        }
        final current = await (db.select(db.localCloudSyncStates)
              ..where((t) => t.id.equals(accountId)))
            .getSingleOrNull();
        if (current != null) return;
        await db.into(db.localCloudSyncStates).insert(
          LocalCloudSyncStatesCompanion.insert(
            id: Value(accountId),
            accountId: Value(accountId),
            deviceId: 'dev-${_uuid.v4()}',
            updatedAt: now,
          ),
        );
        if (states.isEmpty) {
          await (db.update(db.localCloudMutations)
                ..where((t) => t.accountId.isNull()))
              .write(LocalCloudMutationsCompanion(accountId: Value(accountId)));
        }
        await _seedInitialSyncableState(accountId, now);
      });
      row = await (db.select(db.localCloudSyncStates)
            ..where((t) => t.id.equals(accountId)))
          .getSingle();
    }
    return _state(row);
  }



  Future<void> _seedInitialSyncableState(String accountId, DateTime now) async {
    Future<void> enqueue(String type,String id,Map<String,Object?> payload,DateTime modifiedAt) async {
      final exists=await (db.select(db.localCloudMutations)..where((t)=>t.accountId.equals(accountId)&t.entityType.equals(type)&t.entityId.equals(id)&t.status.equals('pending'))).getSingleOrNull();
      if(exists!=null) return;
      await db.into(db.localCloudMutations).insert(LocalCloudMutationsCompanion.insert(
        id:_uuid.v4(),accountId:Value(accountId),entityType:type,entityId:id,payloadJson:Value(jsonEncode(payload)),clientModifiedAt:modifiedAt.toUtc(),createdAt:now,
      ));
    }
    final profiles=await db.select(db.localAcademicProfiles).get();
    for(final r in profiles){await enqueue('academic_profile',r.id,{'faculty':r.faculty,'program':r.program,'level':r.level,'semester':r.semester,'institution':r.institution},r.updatedAt);}
    final events=await (db.select(db.localAcademicEvents)..where((t)=>t.isActive.equals(true))).get();
    for(final r in events){await enqueue('calendar_event',r.id,{'title':r.title,'kind':r.kind,'startsAt':r.startsAt.toUtc().toIso8601String(),'endsAt':r.endsAt?.toUtc().toIso8601String(),'courseId':r.courseId,'notes':r.notes},r.updatedAt);}
    final timetable=await db.select(db.localTimetableEntries).get();
    for(final r in timetable){await enqueue('timetable_entry',r.id,{'title':r.title,'weekday':r.weekday,'startMinute':r.startMinute,'endMinute':r.endMinute,'courseId':r.courseId,'location':r.location},r.updatedAt);}
    final prefs=await db.select(db.localPlanningPreferences).get();
    for(final r in prefs){await enqueue('planning_preferences',r.id,{
      'dailyBudgetMinutes':r.dailyBudgetMinutes,'maxNotificationsPerDay':r.maxNotificationsPerDay,'quietStartMinute':r.quietStartMinute,'quietEndMinute':r.quietEndMinute,
      'maxContinuousMinutes':r.maxContinuousMinutes,'breakMinutes':r.breakMinutes,'maxCoursesPerDay':r.maxCoursesPerDay,'maxCourseSwitches':r.maxCourseSwitches,
      'targetReadiness':r.targetReadiness,'planningHorizonDays':r.planningHorizonDays,
    },r.updatedAt);}
  }

  @override
  Future<List<CloudMutation>> pendingMutations(String accountId,{int limit = 100}) async {
    final now=DateTime.now().toUtc();
    final rows=await (db.select(db.localCloudMutations)
      ..where((t)=>t.accountId.equals(accountId) & t.status.equals('pending') & (t.nextAttemptAt.isNull() | t.nextAttemptAt.isSmallerOrEqualValue(now)))
      ..orderBy([(t)=>OrderingTerm.asc(t.createdAt)])..limit(limit)).get();
    return rows.map((r)=>CloudMutation(
      id:r.id,entityType:r.entityType,entityId:r.entityId,operation:r.operation,
      payload:Map<String,Object?>.from(jsonDecode(r.payloadJson) as Map),baseVersion:r.baseVersion,
      clientModifiedAt:r.clientModifiedAt,retryCount:r.retryCount,
    )).toList(growable:false);
  }

  @override
  Future<void> applyPushOutcomes(String accountId, List<CloudMutation> mutations, List<PushOutcome> outcomes) async {
    await ensureState(accountId);
    final byId = {for (final mutation in mutations) mutation.id: mutation};
    final seen = <String>{};
    // Check the complete server response before beginning the SQLite transaction.
    if (byId.length != mutations.length || outcomes.length != mutations.length) {
      throw StateError('invalid_push_outcomes');
    }
    for (final outcome in outcomes) {
      if (!byId.containsKey(outcome.mutationId) || !seen.add(outcome.mutationId)) {
        throw StateError('invalid_push_outcomes');
      }
      final mutation = byId[outcome.mutationId]!;
      for (final record in <CloudRecord?>[outcome.record, outcome.canonical]) {
        if (record == null) continue;
        if (record.entityType != mutation.entityType ||
            record.entityId != mutation.entityId ||
            record.version < 1 || record.serverSeq < 0) {
          throw StateError('invalid_push_record');
        }
      }
      if (outcome.disposition == 'conflict' && outcome.canonical == null) {
        throw StateError('missing_canonical_conflict');
      }
      if (!const {'applied', 'duplicate', 'conflict', 'rejected'}.contains(outcome.disposition)) {
        throw StateError('unknown_push_disposition');
      }
    }
    await db.transaction(() async {
      for (final outcome in outcomes) {
        final mutation = byId[outcome.mutationId]!;
        switch (outcome.disposition) {
          case 'applied':
          case 'duplicate':
            await markMutationApplied(accountId, mutation.id, outcome.record);
            break;
          case 'conflict':
            await storeConflict(accountId, mutation, outcome.canonical!, outcome.reason ?? 'conflict');
            await applyRemoteRecord(accountId, outcome.canonical!);
            break;
          case 'rejected':
            await markMutationFailed(accountId, mutation.id, outcome.reason ?? 'rejected');
            break;
        }
      }
    });
  }

  @override
  Future<void> markMutationApplied(String accountId,String mutationId, CloudRecord? record) async {
    await db.transaction(() async {
      await (db.update(db.localCloudMutations)..where((t)=>t.id.equals(mutationId)&t.accountId.equals(accountId))).write(const LocalCloudMutationsCompanion(status:Value('sent'),lastError:Value(null),nextAttemptAt:Value(null)));
      if(record!=null) await _saveVersion(accountId,record);
    });
  }

  @override
  Future<void> markMutationFailed(String accountId,String mutationId, String error) async {
    final row=await (db.select(db.localCloudMutations)..where((t)=>t.id.equals(mutationId)&t.accountId.equals(accountId))).getSingleOrNull();
    if(row==null) return;
    // A semantic rejection from the server is not retried forever. Network errors never reach this
    // method because RunCloudSync keeps the pending mutation untouched when the request itself fails.
    await (db.update(db.localCloudMutations)..where((t)=>t.id.equals(mutationId)&t.accountId.equals(accountId))).write(
      LocalCloudMutationsCompanion(status:const Value('deadLetter'),retryCount:Value(row.retryCount+1),lastError:Value(error),nextAttemptAt:const Value(null)),
    );
  }

  @override
  Future<void> storeConflict(String accountId,CloudMutation mutation, CloudRecord canonical, String reason) async {
    final now=DateTime.now().toUtc();
    await db.transaction(() async {
      await (db.update(db.localCloudMutations)..where((t)=>t.id.equals(mutation.id)&t.accountId.equals(accountId))).write(const LocalCloudMutationsCompanion(status:Value('conflict')));
      await db.into(db.localSyncConflicts).insert(LocalSyncConflictsCompanion.insert(
        id:_uuid.v4(),accountId:Value(accountId),mutationId:mutation.id,entityType:mutation.entityType,entityId:mutation.entityId,
        localPayloadJson:Value(jsonEncode(mutation.payload)),canonicalPayloadJson:Value(jsonEncode(canonical.payload)),
        canonicalVersion:canonical.version,reason:reason,createdAt:now,
      ));
      await _saveVersion(accountId,canonical);
    });
  }

  @override
  Future<void> applyRemoteRecord(String accountId,CloudRecord record) async {
    await ensureState(accountId);
    final known=await (db.select(db.localAccountSyncEntityVersions)..where((t)=>t.accountId.equals(accountId)&t.entityType.equals(record.entityType)&t.entityId.equals(record.entityId))).getSingleOrNull();
    // A canonical record must never regress either the entity version or its
    // global sequence. This can happen when a delayed push response arrives
    // after a newer pull, or during recovery from a compacted snapshot.
    if (known != null &&
        (known.version >= record.version || known.serverSeq >= record.serverSeq)) {
      return;
    }
    await db.transaction(() async {
      // A remote snapshot may arrive while an offline edit for this exact
      // entity is still waiting in the outbox. Track the canonical version,
      // but do not overwrite (or delete) the user's unsent local projection.
      // Conflict mutations are deliberately excluded: their canonical state
      // must be projected for the conflict-resolution workflow.
      final pendingEdit = await (db.select(db.localCloudMutations)
            ..where((t) => t.accountId.equals(accountId) &
                t.entityType.equals(record.entityType) &
                t.entityId.equals(record.entityId) &
                t.status.equals('pending'))
            ..limit(1))
          .getSingleOrNull();
      await _saveVersion(accountId,record);
      if (pendingEdit != null) return;
      final p=record.payload;
      switch(record.entityType){
        case 'academic_profile':
          if(record.deleted){ await (db.delete(db.localAcademicProfiles)..where((t)=>t.id.equals(record.entityId))).go(); break; }
          await db.into(db.localAcademicProfiles).insertOnConflictUpdate(LocalAcademicProfilesCompanion.insert(
            id:record.entityId,faculty:(p['faculty']??'').toString(),program:(p['program']??'').toString(),level:(p['level']??'').toString(),semester:(p['semester']??'').toString(),
            institution:Value(p['institution']?.toString()),updatedAt:record.updatedAt,
          ));
          break;
        case 'calendar_event':
          if(record.deleted){ await (db.delete(db.localAcademicEvents)..where((t)=>t.id.equals(record.entityId))).go(); break; }
          await db.into(db.localAcademicEvents).insertOnConflictUpdate(LocalAcademicEventsCompanion.insert(
            id:record.entityId,courseId:Value(p['courseId']?.toString()),title:(p['title']??'Échéance').toString(),kind:(p['kind']??'personal').toString(),
            startsAt:DateTime.parse(p['startsAt'].toString()).toUtc(),endsAt:Value(p['endsAt']==null?null:DateTime.parse(p['endsAt'].toString()).toUtc()),notes:Value(p['notes']?.toString()),updatedAt:record.updatedAt,
          ));
          break;
        case 'timetable_entry':
          if(record.deleted){ await (db.delete(db.localTimetableEntries)..where((t)=>t.id.equals(record.entityId))).go(); break; }
          await db.into(db.localTimetableEntries).insertOnConflictUpdate(LocalTimetableEntriesCompanion.insert(
            id:record.entityId,courseId:Value(p['courseId']?.toString()),title:(p['title']??'Cours').toString(),weekday:(p['weekday'] as num).toInt(),startMinute:(p['startMinute'] as num).toInt(),endMinute:(p['endMinute'] as num).toInt(),location:Value(p['location']?.toString()),updatedAt:record.updatedAt,
          ));
          break;
        case 'planning_preferences':
          if(record.deleted) break;
          await db.into(db.localPlanningPreferences).insertOnConflictUpdate(LocalPlanningPreferencesCompanion.insert(
            dailyBudgetMinutes:Value(_int(p,'dailyBudgetMinutes',30)),maxNotificationsPerDay:Value(_int(p,'maxNotificationsPerDay',2)),quietStartMinute:Value(_int(p,'quietStartMinute',1320)),quietEndMinute:Value(_int(p,'quietEndMinute',420)),
            maxContinuousMinutes:Value(_int(p,'maxContinuousMinutes',50)),breakMinutes:Value(_int(p,'breakMinutes',10)),maxCoursesPerDay:Value(_int(p,'maxCoursesPerDay',4)),maxCourseSwitches:Value(_int(p,'maxCourseSwitches',5)),
            targetReadiness:Value(_int(p,'targetReadiness',80)),planningHorizonDays:Value(_int(p,'planningHorizonDays',14)),updatedAt:record.updatedAt,
          ));
          break;
        case 'reading_progress':
          if(record.deleted){ await (db.delete(db.localReadingProgress)..where((t)=>t.documentId.equals(record.entityId))).go(); break; }
          await db.into(db.localReadingProgress).insertOnConflictUpdate(LocalReadingProgressCompanion.insert(
            documentId:record.entityId,pageNumber:Value(_int(p,'page',1)),pageProgress:Value(_double(p,'progress',0)),totalPages:Value(_int(p,'totalPages',0)),lastOpenedAt:record.updatedAt,secondsSpent:Value(_int(p,'secondsSpent',0)),
          ));
          break;
        case 'course_follow':
          if(record.deleted){ await (db.delete(db.localLibraryCourseFollows)..where((t)=>t.courseId.equals(record.entityId))).go(); break; }
          await db.into(db.localLibraryCourseFollows).insertOnConflictUpdate(LocalLibraryCourseFollowsCompanion.insert(
            courseId:record.entityId,followed:Value(p['followed'] == true),updatedAt:record.updatedAt,
          ));
          break;
        case 'objective_mastery':
          if(record.deleted){ await (db.delete(db.localObjectiveMastery)..where((t)=>t.objectiveId.equals(record.entityId))).go(); break; }
          await db.into(db.localObjectiveMastery).insertOnConflictUpdate(LocalObjectiveMasteryCompanion.insert(
            objectiveId:record.entityId,mastery:Value(_double(p,'mastery',0)),evidenceCount:Value(_int(p,'evidenceCount',0)),updatedAt:record.updatedAt,
          ));
          break;
        default:
          // Append-only telemetry remains in the canonical version ledger. It is never projected
          // into private document tables, preserving the sync privacy boundary.
          break;
      }
    });
  }

  @override
  Future<void> applyCanonicalPage(String accountId, List<CloudRecord> records, int cursor,
      {required int retainedFloor, bool reset = false, DateTime? bootstrappedAt}) async {
    // Validate the complete page before any destructive reset or projection.
    // In particular, a malformed page must not erase a healthy offline cache.
    if (cursor < 0 || retainedFloor < 0 || retainedFloor > cursor) {
      throw StateError('invalid_canonical_page_cursor');
    }
    final identities = <String>{};
    for (final record in records) {
      if (record.version < 1 || record.serverSeq < 0 ||
          record.serverSeq > cursor ||
          (reset && !identities.add(jsonEncode([record.entityType, record.entityId])))) {
        throw StateError('invalid_canonical_page_record');
      }
    }
    await ensureState(accountId);
    // A failed projection or SQLite constraint must roll back both the
    // canonical reset and all applied records, including the cursor.
    await db.transaction(() async {
      if (reset) await prepareCanonicalReset(accountId);
      for (final record in records) {
        await applyRemoteRecord(accountId, record);
      }
      await updateCursor(accountId, cursor,
          retainedFloor: retainedFloor, bootstrappedAt: bootstrappedAt);
    });
  }

  @override
  Future<void> prepareCanonicalReset(String accountId) async {
    await ensureState(accountId);
    final versions=await (db.select(db.localAccountSyncEntityVersions)..where((t)=>t.accountId.equals(accountId))).get();
    final pending=await (db.select(db.localCloudMutations)..where((t)=>t.accountId.equals(accountId)&(t.status.equals('pending')|t.status.equals('conflict')))).get();
    final protectedKeys={for(final m in pending)'${m.entityType}:${m.entityId}'};
    await db.transaction(() async {
      for(final v in versions){
        if(protectedKeys.contains('${v.entityType}:${v.entityId}')) continue;
        switch(v.entityType){
          case 'academic_profile': await (db.delete(db.localAcademicProfiles)..where((t)=>t.id.equals(v.entityId))).go(); break;
          case 'calendar_event': await (db.delete(db.localAcademicEvents)..where((t)=>t.id.equals(v.entityId))).go(); break;
          case 'timetable_entry': await (db.delete(db.localTimetableEntries)..where((t)=>t.id.equals(v.entityId))).go(); break;
          case 'reading_progress': await (db.delete(db.localReadingProgress)..where((t)=>t.documentId.equals(v.entityId))).go(); break;
          case 'objective_mastery': await (db.delete(db.localObjectiveMastery)..where((t)=>t.objectiveId.equals(v.entityId))).go(); break;
          case 'course_follow': await (db.delete(db.localLibraryCourseFollows)..where((t)=>t.courseId.equals(v.entityId))).go(); break;
        }
      }
      // Retain version baselines for protected offline edits. Removing them
      // would allow an older bootstrap record to replace their canonical
      // baseline, causing false conflicts on the next push.
      for (final version in versions) {
        if (protectedKeys.contains('${version.entityType}:${version.entityId}')) continue;
        await (db.delete(db.localAccountSyncEntityVersions)
              ..where((t) => t.accountId.equals(accountId) &
                  t.entityType.equals(version.entityType) &
                  t.entityId.equals(version.entityId)))
            .go();
      }
    });
  }

  Future<void> _saveVersion(String accountId,CloudRecord record) async {
    final existing = await (db.select(db.localAccountSyncEntityVersions)
          ..where((t) => t.accountId.equals(accountId) &
              t.entityType.equals(record.entityType) &
              t.entityId.equals(record.entityId)))
        .getSingleOrNull();
    // This helper is also called from push acknowledgements and conflict
    // bookkeeping. Those paths must not roll back a newer pull's ledger.
    if (existing != null &&
        (existing.version >= record.version ||
            existing.serverSeq >= record.serverSeq)) return;
    await db.into(db.localAccountSyncEntityVersions).insertOnConflictUpdate(LocalAccountSyncEntityVersionsCompanion.insert(
      accountId:accountId,entityType:record.entityType,entityId:record.entityId,version:record.version,serverSeq:record.serverSeq,
      payloadJson:Value(jsonEncode(record.payload)),deleted:Value(record.deleted),updatedAt:record.updatedAt,
    ));
  }

  int _int(Map<String,Object?> p,String key,int fallback)=>p[key] is num?(p[key] as num).toInt():fallback;
  double _double(Map<String,Object?> p,String key,double fallback)=>p[key] is num?(p[key] as num).toDouble():fallback;

  @override
  Future<void> updateCursor(String accountId,int cursor,{int? retainedFloor,DateTime? syncedAt,DateTime? bootstrappedAt,String? lastError}) async {
    await ensureState(accountId);
    if (cursor < 0 || (retainedFloor != null &&
        (retainedFloor < 0 || retainedFloor > cursor))) {
      throw StateError('invalid_sync_cursor');
    }
    final now=DateTime.now().toUtc();
    await db.transaction(() async {
      final state = await (db.select(db.localCloudSyncStates)
            ..where((t) => t.id.equals(accountId))).getSingle();
      // A reset/bootstrap can legitimately move the cursor backwards after
      // server compaction; ordinary pulls and error paths cannot.
      if (bootstrappedAt == null && cursor < state.serverCursor) {
        throw StateError('sync_cursor_regression');
      }
      await (db.update(db.localCloudSyncStates)..where((t)=>t.id.equals(accountId))).write(LocalCloudSyncStatesCompanion(
      serverCursor:Value(cursor),retainedFloor:retainedFloor==null?const Value.absent():Value(retainedFloor),
      lastSyncAt:syncedAt==null?const Value.absent():Value(syncedAt),lastBootstrapAt:bootstrappedAt==null?const Value.absent():Value(bootstrappedAt),
      lastError:Value(lastError),updatedAt:Value(now),
      ));
    });
  }

  @override
  Future<void> recordSyncError(String accountId, String error) async {
    // Only update the diagnostic field. In particular, never overwrite the
    // checkpoint persisted atomically by applyCanonicalPage.
    await ensureState(accountId);
    await (db.update(db.localCloudSyncStates)
          ..where((t) => t.id.equals(accountId)))
        .write(LocalCloudSyncStatesCompanion(
          lastError: Value(error),
          updatedAt: Value(DateTime.now().toUtc()),
        ));
  }

  @override
  Future<void> markRegistered(String accountId) async {
    await ensureState(accountId);
    await (db.update(db.localCloudSyncStates)..where((t)=>t.id.equals(accountId))).write(LocalCloudSyncStatesCompanion(registered:const Value(true),updatedAt:Value(DateTime.now().toUtc())));
  }

  @override
  Future<void> markAcknowledged(String accountId,int cursor) async {
    await ensureState(accountId);
    await db.transaction(() async {
      final row=await (db.select(db.localCloudSyncStates)..where((t)=>t.id.equals(accountId))).getSingle();
      if (cursor < 0 || cursor > row.serverCursor) {
        throw StateError('invalid_acknowledgement_cursor');
      }
      final next=cursor>row.ackedCursor?cursor:row.ackedCursor;
      await (db.update(db.localCloudSyncStates)..where((t)=>t.id.equals(accountId))).write(LocalCloudSyncStatesCompanion(ackedCursor:Value(next),updatedAt:Value(DateTime.now().toUtc())));
    });
  }

  @override
  Future<void> resolveConflict(String accountId,String conflictId,{required bool keepLocal}) async {
    await ensureState(accountId);
    final row=await (db.select(db.localSyncConflicts)..where((t)=>t.id.equals(conflictId)&t.accountId.equals(accountId))).getSingleOrNull();
    if(row==null || row.resolvedAt!=null) return;
    final now=DateTime.now().toUtc();
    await db.transaction(() async {
      if(keepLocal){
        await db.into(db.localCloudMutations).insert(LocalCloudMutationsCompanion.insert(
          id:_uuid.v4(),accountId:Value(accountId),entityType:row.entityType,entityId:row.entityId,
          payloadJson:Value(row.localPayloadJson),baseVersion:Value(row.canonicalVersion),clientModifiedAt:now,createdAt:now,
        ));
      }
      await (db.update(db.localSyncConflicts)..where((t)=>t.id.equals(conflictId)&t.accountId.equals(accountId))).write(LocalSyncConflictsCompanion(resolvedAt:Value(now)));
    });
  }

  @override
  Stream<CloudSyncState?> watchState(String accountId)=> (db.select(db.localCloudSyncStates)..where((t)=>t.id.equals(accountId))).watchSingleOrNull().map((r)=>r==null?null:_state(r));

  @override
  Stream<List<SyncConflictView>> watchOpenConflicts(String accountId){
    final q=db.select(db.localSyncConflicts)..where((t)=>t.accountId.equals(accountId)&t.resolvedAt.isNull())..orderBy([(t)=>OrderingTerm.desc(t.createdAt)]);
    return q.watch().map((rows)=>rows.map((r)=>SyncConflictView(id:r.id,entityType:r.entityType,entityId:r.entityId,reason:r.reason,createdAt:r.createdAt)).toList(growable:false));
  }

  @override
  Stream<SyncDiagnostics> watchDiagnostics(String accountId) {
    final mutations=(db.select(db.localCloudMutations)..where((t)=>t.accountId.equals(accountId))).watch();
    final conflicts=(db.select(db.localSyncConflicts)..where((t)=>t.accountId.equals(accountId)&t.resolvedAt.isNull())).watch();
    return mutations.asyncExpand((rows) => conflicts.map((conflictRows) {
      final pendingRows=rows.where((r)=>r.status=='pending').toList(growable:false);
      final oldest=pendingRows.isEmpty?null:pendingRows.map((r)=>r.createdAt).reduce((a,b)=>a.isBefore(b)?a:b);
      return SyncDiagnostics(
        pending:pendingRows.length,
        deadLetters:rows.where((r)=>r.status=='deadLetter').length,
        openConflicts:conflictRows.length,
        oldestPendingAt:oldest,
      );
    }));
  }

  CloudSyncState _state(LocalCloudSyncState r)=>CloudSyncState(
    deviceId:r.deviceId,accountId:r.accountId,serverCursor:r.serverCursor,ackedCursor:r.ackedCursor,retainedFloor:r.retainedFloor,
    registered:r.registered,lastSyncAt:r.lastSyncAt,lastBootstrapAt:r.lastBootstrapAt,lastError:r.lastError,
  );
}

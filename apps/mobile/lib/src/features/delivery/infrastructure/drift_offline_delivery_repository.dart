import 'package:drift/drift.dart';
import '../../../core/security/local_account_access.dart';
import '../../../core/database/app_database.dart';
import '../application/delivery_repository.dart';
import '../domain/delivery.dart';

class DriftOfflineDeliveryRepository implements OfflineDeliveryRepository {
  DriftOfflineDeliveryRepository(this.db); final AppDatabase db;
  final LocalAccountAccess _access = LocalAccountAccess();

  Future<T> _read<T>(Future<T> Function() operation) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    final result = await operation();
    await _access.assertUnchanged(revision, owned: true);
    return result;
  }

  Future<T> _write<T>(Future<T> Function() operation) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    return db.transaction(() async {
      final result = await operation();
      await _access.assertUnchanged(revision, owned: true);
      return result;
    });
  }

  OfflineResourceState _map(LocalLibraryDownloadState r)=>OfflineResourceState(
    resourceId:r.resourceId,state:r.state,bytesDownloaded:r.bytesDownloaded,totalBytes:r.totalBytes,
    localUri:r.localUri,tempUri:r.tempUri,checksumSha256:r.checksumSha256,etag:r.etag,lastError:r.lastError,
    verifiedAt:r.verifiedAt,lastAccessedAt:r.lastAccessedAt,pinned:r.pinned,
  );

  @override Stream<OfflineResourceState?> watchState(String id)=>
    _access.protect((db.select(db.localLibraryDownloadStates)..where((t)=>t.resourceId.equals(id))).watchSingleOrNull().map((r)=>r==null?null:_map(r)), owned: true);
  @override Stream<List<OfflineResourceState>> watchAll()=>_access.protect(db.select(db.localLibraryDownloadStates).watch().map((rows)=>rows.map(_map).toList(growable:false)), owned: true);
  @override Future<OfflineResourceState?> getState(String id) async {
    return _read(() async {final r=await (db.select(db.localLibraryDownloadStates)..where((t)=>t.resourceId.equals(id))).getSingleOrNull();return r==null?null:_map(r);
    });
  }

  @override Future<ContentCachePolicy> loadPolicy() async {
    return _read(() async {
    final r=await (db.select(db.localContentCachePolicies)..where((t)=>t.id.equals('default'))).getSingleOrNull();
    if(r==null){ final d=ContentCachePolicy(maxCacheBytes:2147483648,minFreeBytes:536870912,wifiOnlyLargeDownloads:true,largeDownloadThresholdBytes:52428800,autoCleanup:true,keepFollowedCourses:true); await savePolicy(d); return d; }
    return ContentCachePolicy(maxCacheBytes:r.maxCacheBytes,minFreeBytes:r.minFreeBytes,wifiOnlyLargeDownloads:r.wifiOnlyLargeDownloads,largeDownloadThresholdBytes:r.largeDownloadThresholdBytes,autoCleanup:r.autoCleanup,keepFollowedCourses:r.keepFollowedCourses);
  
    });
  }
  @override Future<void> savePolicy(ContentCachePolicy p) async {
    await _write(() async => db.into(db.localContentCachePolicies).insertOnConflictUpdate(LocalContentCachePoliciesCompanion.insert(
    id:const Value('default'),maxCacheBytes:Value(p.maxCacheBytes),minFreeBytes:Value(p.minFreeBytes),wifiOnlyLargeDownloads:Value(p.wifiOnlyLargeDownloads),largeDownloadThresholdBytes:Value(p.largeDownloadThresholdBytes),autoCleanup:Value(p.autoCleanup),keepFollowedCourses:Value(p.keepFollowedCourses),updatedAt:DateTime.now().toUtc(),
  )));
  }

  @override Future<void> markDownloading({required String resourceId,required int bytesDownloaded,required int totalBytes,String? etag,String? checksumSha256,String? tempUri}) async {
    await _write(() async {
    final old=await (db.select(db.localLibraryDownloadStates)..where((t)=>t.resourceId.equals(resourceId))).getSingleOrNull();
    await db.into(db.localLibraryDownloadStates).insertOnConflictUpdate(LocalLibraryDownloadStatesCompanion.insert(
      resourceId:resourceId,state:const Value('downloading'),bytesDownloaded:Value(bytesDownloaded),totalBytes:Value(totalBytes),etag:Value(etag),checksumSha256:Value(checksumSha256),tempUri:Value(tempUri),
      pinned:Value(old?.pinned??false),retryCount:Value(old?.retryCount??0),updatedAt:DateTime.now().toUtc(),
    ));
  
    });
  }
  @override Future<void> markReady({required String resourceId,required String localUri,required int totalBytes,String? etag,String? checksumSha256}) async {
    await _write(() async {
    final now=DateTime.now().toUtc(); final old=await (db.select(db.localLibraryDownloadStates)..where((t)=>t.resourceId.equals(resourceId))).getSingleOrNull();
    await db.into(db.localLibraryDownloadStates).insertOnConflictUpdate(LocalLibraryDownloadStatesCompanion.insert(
      resourceId:resourceId,state:const Value('ready'),localUri:Value(localUri),checksumSha256:Value(checksumSha256),etag:Value(etag),bytesDownloaded:Value(totalBytes),totalBytes:Value(totalBytes),
      pinned:Value(old?.pinned??false),downloadedAt:Value(now),verifiedAt:Value(now),lastAccessedAt:Value(now),updatedAt:now,
    ));
  
    });
  }
  @override Future<void> markFailed(String resourceId,String error,{bool incrementRetry=true}) async {
    await _write(() async {
    final old=await (db.select(db.localLibraryDownloadStates)..where((t)=>t.resourceId.equals(resourceId))).getSingleOrNull(); final now=DateTime.now().toUtc();
    await db.into(db.localLibraryDownloadStates).insertOnConflictUpdate(LocalLibraryDownloadStatesCompanion.insert(
      resourceId:resourceId,state:const Value('failed'),bytesDownloaded:Value(old?.bytesDownloaded??0),totalBytes:Value(old?.totalBytes),localUri:Value(old?.localUri),tempUri:Value(old?.tempUri),checksumSha256:Value(old?.checksumSha256),etag:Value(old?.etag),pinned:Value(old?.pinned??false),retryCount:Value((old?.retryCount??0)+(incrementRetry?1:0)),lastError:Value(error),updatedAt:now,
    ));
  
    });
  }
  @override Future<void> reset(String id) async {
    await _write(() async => (db.delete(db.localLibraryDownloadStates)..where((t)=>t.resourceId.equals(id))).go());
  }
  @override Future<void> touch(String id) async {
    await _write(() async => (db.update(db.localLibraryDownloadStates)..where((t)=>t.resourceId.equals(id))).write(LocalLibraryDownloadStatesCompanion(lastAccessedAt:Value(DateTime.now().toUtc()),updatedAt:Value(DateTime.now().toUtc()))));
  }
  @override Future<void> setPinned(String id,bool pinned) async {
    await _write(() async => (db.update(db.localLibraryDownloadStates)..where((t)=>t.resourceId.equals(id))).write(LocalLibraryDownloadStatesCompanion(pinned:Value(pinned),updatedAt:Value(DateTime.now().toUtc()))));
  }
  @override Future<int> readyBytes() async {
    return _read(() async {
    final rows=await (db.select(db.localLibraryDownloadStates)..where((t)=>t.state.equals('ready'))).get();
    return rows.fold<int>(0,(sum,r)=>sum+(r.totalBytes??0));
  
    });
  }

  @override Future<List<CacheCandidate>> cacheCandidates() async {
    return _read(() async {
    final downloads=await (db.select(db.localLibraryDownloadStates)..where((t)=>t.state.equals('ready'))).get();
    final resources=await db.select(db.localLibraryResources).get();
    final versions=await db.select(db.localLibraryCourseVersions).get();
    final follows=await db.select(db.localLibraryCourseFollows).get();
    final versionCourse={for(final v in versions)v.id:v.courseId};
    final followed={for(final f in follows)if(f.followed)f.courseId};
    final resourceVersion={for(final r in resources)r.id:r.versionId};
    return downloads.map((d){final cid=versionCourse[resourceVersion[d.resourceId]];return CacheCandidate(resourceId:d.resourceId,sizeBytes:d.totalBytes??0,lastAccessedAt:d.lastAccessedAt,pinned:d.pinned,followed:cid!=null&&followed.contains(cid));}).toList(growable:false);
  
    });
  }

  @override Future<void> enqueue({required String courseId,required String resourceId,int priority=50}) async {
    await _write(() async {
    final existing=await (db.select(db.localDownloadQueueItems)..where((t)=>t.resourceId.equals(resourceId))).getSingleOrNull();
    if(existing!=null && const {'queued','running'}.contains(existing.state)) return;
    final now=DateTime.now().toUtc();
    await db.into(db.localDownloadQueueItems).insertOnConflictUpdate(LocalDownloadQueueItemsCompanion.insert(
      id:'dl-$resourceId',courseId:courseId,resourceId:resourceId,priority:Value(priority),state:const Value('queued'),createdAt:existing?.createdAt??now,updatedAt:now,
    ));
  
    });
  }
  @override Future<QueuedDownload?> nextQueued() async {
    return _read(() async {
    final now=DateTime.now().toUtc();
    final rows=await (db.select(db.localDownloadQueueItems)..where((t)=>t.state.equals('queued'))..orderBy([(t)=>OrderingTerm.desc(t.priority),(t)=>OrderingTerm.asc(t.createdAt)])).get();
    for(final r in rows){if(r.nextAttemptAt==null||!r.nextAttemptAt!.isAfter(now))return QueuedDownload(id:r.id,courseId:r.courseId,resourceId:r.resourceId,priority:r.priority,state:r.state,attempts:r.attempts,nextAttemptAt:r.nextAttemptAt,lastError:r.lastError);}
    return null;
  
    });
  }
  @override Future<void> updateQueue(String id,{required String state,int? attempts,DateTime? nextAttemptAt,String? lastError}) async {
    await _write(() async => (db.update(db.localDownloadQueueItems)..where((t)=>t.id.equals(id))).write(LocalDownloadQueueItemsCompanion(state:Value(state),attempts:attempts==null?const Value.absent():Value(attempts),nextAttemptAt:Value(nextAttemptAt),lastError:Value(lastError),updatedAt:Value(DateTime.now().toUtc()))));
  }
  @override Future<void> removeQueueForResource(String resourceId) async {
    await _write(() async => (db.delete(db.localDownloadQueueItems)..where((t)=>t.resourceId.equals(resourceId))).go());
  }

}

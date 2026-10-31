import '../../library/domain/library.dart';
import '../../library/application/library_repository.dart';
import '../domain/delivery.dart';
import 'download_resource.dart';

abstract interface class DeliveryRemoteGateway {
  Future<DeliveryGrantView> grant({required String resourceId,required String deliveryToken});
}

abstract interface class OfflineDeliveryRepository {
  Stream<OfflineResourceState?> watchState(String resourceId);
  Stream<List<OfflineResourceState>> watchAll();
  Future<OfflineResourceState?> getState(String resourceId);
  Future<ContentCachePolicy> loadPolicy();
  Future<void> savePolicy(ContentCachePolicy policy);
  Future<void> markDownloading({required String resourceId,required int bytesDownloaded,required int totalBytes,String? etag,String? checksumSha256,String? tempUri});
  Future<void> markReady({required String resourceId,required String localUri,required int totalBytes,String? etag,String? checksumSha256});
  Future<void> markFailed(String resourceId,String error,{bool incrementRetry=true});
  Future<void> reset(String resourceId);
  Future<void> touch(String resourceId);
  Future<void> setPinned(String resourceId,bool pinned);
  Future<int> readyBytes();
  Future<List<CacheCandidate>> cacheCandidates();
  Future<void> enqueue({required String courseId,required String resourceId,int priority=50});
  Future<QueuedDownload?> nextQueued();
  Future<void> updateQueue(String id,{required String state,int? attempts,DateTime? nextAttemptAt,String? lastError});
  Future<void> removeQueueForResource(String resourceId);
}

abstract interface class OfflineResourceStore {
  Future<int> partialLength(String resourceId);
  Future<void> resetPartial(String resourceId);
  Future<void> append(String resourceId,List<int> bytes);
  Future<String> finalize(String resourceId);
  Future<String> sha256Hex(String resourceId,{required bool finalized});
  Future<void> delete(String resourceId);
  Future<String?> finalUri(String resourceId);
}


class RunCacheCleanup {
  const RunCacheCleanup({required this.local,required this.store});
  final OfflineDeliveryRepository local; final OfflineResourceStore store;
  Future<int> call() async {
    final policy=await local.loadPolicy(); if(!policy.autoCleanup) return 0;
    final current=await local.readyBytes(); if(current<=policy.maxCacheBytes) return 0;
    final ids=const CacheEvictionPlanner().plan(candidates:await local.cacheCandidates(),currentBytes:current,targetBytes:policy.maxCacheBytes,keepFollowed:policy.keepFollowedCourses);
    var removed=0;
    for(final id in ids){ final s=await local.getState(id); await store.delete(id); await local.reset(id); removed+=s?.totalBytes??0; }
    return removed;
  }
}


class RunDownloadQueue {
  RunDownloadQueue({required this.local,required this.remoteLibrary,required this.downloader});
  final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final DownloadResource downloader;
  Future<int> drain({int limit=2}) async {
    var done=0; final manifests=<String,LibraryManifest>{};
    for(var i=0;i<limit;i++){
      final q=await local.nextQueued(); if(q==null)break;
      await local.updateQueue(q.id,state:'running');
      try{
        final manifest=manifests[q.courseId] ??= await remoteLibrary.loadManifest(q.courseId);
        final resource=manifest.resources.firstWhere((r)=>r.id==q.resourceId);
        await downloader.call(resource);
        await local.removeQueueForResource(q.resourceId); done++;
      }catch(e){
        // A device going offline is not a failed resource. Keep the job queued
        // without consuming its five retry attempts; retry on the next drain.
        if (e is StateError && e.message == 'network_unavailable') {
          await local.updateQueue(q.id,state:'queued',attempts:q.attempts,
            nextAttemptAt:DateTime.now().toUtc().add(const Duration(seconds:30)),
            lastError:'En attente de connexion réseau');
          break;
        }
        final attempts=q.attempts+1; final dead=attempts>=5;
        await local.updateQueue(q.id,state:dead?'failed':'queued',attempts:attempts,nextAttemptAt:dead?null:DateTime.now().toUtc().add(Duration(seconds:1 << (attempts > 5 ? 5 : attempts))),lastError:e.toString());
        if(!dead) break;
      }
    }
    return done;
  }
}


class QueueCourseOffline {
  const QueueCourseOffline({required this.local,required this.remoteLibrary,required this.queue});
  final OfflineDeliveryRepository local; final LibraryRemoteGateway remoteLibrary; final RunDownloadQueue queue;
  Future<int> call(String courseId,{int immediate=2}) async {
    final manifest=await remoteLibrary.loadManifest(courseId);
    var count=0;
    for(final r in manifest.resources){
      if(r.access=='available' && r.offlineAllowed){await local.enqueue(courseId:courseId,resourceId:r.id,priority:70);count++;}
    }
    if(count>0) await queue.drain(limit:immediate.clamp(0,count).toInt());
    return count;
  }
}

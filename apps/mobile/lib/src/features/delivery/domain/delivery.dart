class DeliveryGrantView {
  const DeliveryGrantView({
    required this.resourceId,
    required this.url,
    required this.expiresAt,
    required this.sizeBytes,
    required this.supportsRange,required this.requiresAppAuth,
    this.checksumSha256,
    this.etag,
    this.contentType,
  });
  final String resourceId,url;
  final DateTime expiresAt;
  final int sizeBytes;
  final bool supportsRange,requiresAppAuth;
  final String? checksumSha256,etag,contentType;
}

class OfflineResourceState {
  const OfflineResourceState({
    required this.resourceId,required this.state,required this.bytesDownloaded,
    this.totalBytes,this.localUri,this.tempUri,this.checksumSha256,this.etag,
    this.lastError,this.verifiedAt,this.lastAccessedAt,this.pinned=false,
  });
  final String resourceId,state;
  final int bytesDownloaded;
  final int? totalBytes;
  final String? localUri,tempUri,checksumSha256,etag,lastError;
  final DateTime? verifiedAt,lastAccessedAt;
  final bool pinned;

  double get progress => (totalBytes==null || totalBytes==0) ? 0 : (bytesDownloaded/totalBytes!).clamp(0,1);
  bool get ready => state=='ready' && localUri!=null && verifiedAt!=null;
}

class ContentCachePolicy {
  const ContentCachePolicy({
    required this.maxCacheBytes,required this.minFreeBytes,required this.wifiOnlyLargeDownloads,
    required this.largeDownloadThresholdBytes,required this.autoCleanup,required this.keepFollowedCourses,
  });
  final int maxCacheBytes,minFreeBytes,largeDownloadThresholdBytes;
  final bool wifiOnlyLargeDownloads,autoCleanup,keepFollowedCourses;
}

class CacheCandidate {
  const CacheCandidate({required this.resourceId,required this.sizeBytes,required this.lastAccessedAt,required this.pinned,required this.followed});
  final String resourceId;
  final int sizeBytes;
  final DateTime? lastAccessedAt;
  final bool pinned,followed;
}

class OfflineAccessPolicy {
  const OfflineAccessPolicy();
  bool canOpen({required bool premiumResource,required bool premium,required DateTime? premiumUntil,required DateTime offlineValidUntil,DateTime? now}){
    if(!premiumResource) return true;
    final t=(now??DateTime.now()).toUtc();
    return premium && premiumUntil!=null && premiumUntil.toUtc().isAfter(t) && offlineValidUntil.toUtc().isAfter(t);
  }
}

class CacheEvictionPlanner {
  const CacheEvictionPlanner();
  List<String> plan({required List<CacheCandidate> candidates,required int currentBytes,required int targetBytes,required bool keepFollowed}){
    if(currentBytes<=targetBytes) return const [];
    final removable=candidates.where((c)=>!c.pinned && !(keepFollowed && c.followed)).toList()
      ..sort((a,b){
        final at=a.lastAccessedAt??DateTime.fromMillisecondsSinceEpoch(0,isUtc:true);
        final bt=b.lastAccessedAt??DateTime.fromMillisecondsSinceEpoch(0,isUtc:true);
        return at.compareTo(bt);
      });
    var remaining=currentBytes; final out=<String>[];
    for(final c in removable){ if(remaining<=targetBytes) break; out.add(c.resourceId); remaining-=c.sizeBytes; }
    return out;
  }
}


class QueuedDownload {
  const QueuedDownload({required this.id,required this.courseId,required this.resourceId,required this.priority,required this.state,required this.attempts,this.nextAttemptAt,this.lastError});
  final String id,courseId,resourceId,state; final int priority,attempts; final DateTime? nextAttemptAt; final String? lastError;
}

import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import '../../identity/application/identity_repository.dart';
import '../../library/domain/library.dart';
import '../application/delivery_repository.dart';
import '../domain/delivery.dart';

class DownloadResource {
  DownloadResource({required this.remote,required this.local,required this.store,required this.identity,Dio? dio,Connectivity? connectivity}):_dio=dio??Dio(),_connectivity=connectivity??Connectivity();
  final DeliveryRemoteGateway remote; final OfflineDeliveryRepository local; final OfflineResourceStore store; final IdentityRepository identity; final Dio _dio; final Connectivity _connectivity;

  Future<void> call(LibraryResourceView resource,{bool force=false}) async{
    if(resource.access!='available') throw StateError('resource_locked');
    if(!resource.offlineAllowed) throw StateError('resource_offline_not_allowed');
    final token=resource.deliveryToken; if(token==null||token.isEmpty) throw StateError('delivery_token_missing');
    final connection=await _connectivity.checkConnectivity();
    if(connection.isEmpty || connection.contains(ConnectivityResult.none)) throw StateError('network_unavailable');
    final policy=await local.loadPolicy();
    if(policy.wifiOnlyLargeDownloads && (resource.sizeBytes??0)>=policy.largeDownloadThresholdBytes && !force){
      if(!connection.contains(ConnectivityResult.wifi) && !connection.contains(ConnectivityResult.ethernet)) throw StateError('large_download_requires_wifi');
    }
    final grant=await remote.grant(resourceId:resource.id,deliveryToken:token);
    final currentCache=await local.readyBytes();
    if(currentCache+grant.sizeBytes>policy.maxCacheBytes){
      if(policy.autoCleanup){
        final ids=const CacheEvictionPlanner().plan(candidates:await local.cacheCandidates(),currentBytes:currentCache,targetBytes:(policy.maxCacheBytes-grant.sizeBytes).clamp(0,policy.maxCacheBytes).toInt(),keepFollowed:policy.keepFollowedCourses);
        for(final id in ids){await store.delete(id);await local.reset(id);}
      }
      if(await local.readyBytes()+grant.sizeBytes>policy.maxCacheBytes) throw StateError('offline_cache_limit_exceeded');
    }
    final previous=await local.getState(resource.id);
    var offset=await store.partialLength(resource.id);
    if(offset>0 && previous?.etag!=null && grant.etag!=null && previous!.etag!=grant.etag){await store.resetPartial(resource.id);offset=0;}
    if(offset>grant.sizeBytes){await store.resetPartial(resource.id);offset=0;}
    await local.markDownloading(resourceId:resource.id,bytesDownloaded:offset,totalBytes:grant.sizeBytes,etag:grant.etag,checksumSha256:grant.checksumSha256);
    try{
      final headers=<String,dynamic>{'Accept':'application/octet-stream'};
      if(grant.requiresAppAuth){ var s=await identity.currentSession(); if(s==null) throw StateError('delivery_auth_required'); if(s.accessExpired)s=await identity.refresh(); headers['Authorization']='Bearer ${s.accessToken}'; }
      if(offset>0 && grant.supportsRange){headers['Range']='bytes=$offset-'; if(grant.etag!=null)headers['If-Range']=grant.etag;}
      final response=await _dio.get<ResponseBody>(grant.url,options:Options(responseType:ResponseType.stream,headers:headers,validateStatus:(s)=>s==200||s==206));
      if(offset>0 && response.statusCode==200){await store.resetPartial(resource.id);offset=0;}
      if(offset>0 && response.statusCode==206){
        final contentRange=response.headers.value(Headers.contentRangeHeader);
        if(!_validContentRange(contentRange,offset,grant.sizeBytes)){
          await store.resetPartial(resource.id);
          throw StateError('download_content_range_mismatch');
        }
      }
      var written=offset; var nextReport=written+512*1024;
      await for(final chunk in response.data!.stream){await store.append(resource.id,chunk);written+=chunk.length;if(written>=nextReport){await local.markDownloading(resourceId:resource.id,bytesDownloaded:written,totalBytes:grant.sizeBytes,etag:grant.etag,checksumSha256:grant.checksumSha256);nextReport=written+512*1024;}}
      if(written!=grant.sizeBytes) throw StateError('download_size_mismatch:$written/${grant.sizeBytes}');
      if(grant.checksumSha256!=null){final actual=await store.sha256Hex(resource.id,finalized:false);if(actual.toLowerCase()!=grant.checksumSha256!.toLowerCase()){await store.resetPartial(resource.id);throw StateError('download_checksum_mismatch');}}
      final uri=await store.finalize(resource.id);
      await local.markReady(resourceId:resource.id,localUri:uri,totalBytes:grant.sizeBytes,etag:grant.etag,checksumSha256:grant.checksumSha256);
    }catch(e){
      final transient=e is DioException && const {
        DioExceptionType.connectionTimeout,
        DioExceptionType.sendTimeout,
        DioExceptionType.receiveTimeout,
        DioExceptionType.connectionError,
      }.contains(e.type);
      await local.markFailed(resource.id,e.toString(),incrementRetry:!transient);
      rethrow;
    }
  }

  static bool _validContentRange(String? value,int offset,int total){
    if(value==null)return false;
    final match=RegExp(r'^bytes (\d+)-(\d+)/(\d+)$').firstMatch(value.trim());
    if(match==null)return false;
    final start=int.tryParse(match.group(1)!); final end=int.tryParse(match.group(2)!); final length=int.tryParse(match.group(3)!);
    return start!=null && end!=null && length!=null && start==offset && length==total && end>=start && end<total;
  }
}

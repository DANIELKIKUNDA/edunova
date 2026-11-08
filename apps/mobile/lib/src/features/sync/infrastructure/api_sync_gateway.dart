import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../identity/application/identity_repository.dart';
import '../application/cloud_sync_repository.dart';
import '../domain/cloud_sync.dart';

class ApiSyncGateway implements CloudSyncRemoteGateway {
  ApiSyncGateway({required ApiClient api, required IdentityRepository identity}) : _api = api, _identity = identity;
  final ApiClient _api;
  final IdentityRepository _identity;

  Future<Options> _auth() async {
    var session = await _identity.currentSession();
    if (session == null) throw StateError('authentication_required');
    if (session.accessExpired) session = await _identity.refresh();
    return Options(headers: {'Authorization': 'Bearer ${session.accessToken}'});
  }

  @override
  Future<void> registerDevice({required String deviceId, required String name, required String platform, required String appVersion}) async {
    await _api.dio.post('/v1/sync/devices', data: {'device_id':deviceId,'name':name,'platform':platform,'app_version':appVersion}, options: await _auth());
  }

  @override
  Future<int> acknowledge({required String deviceId, required int cursor}) async {
    final r=await _api.dio.post('/v1/sync/ack',data:{'device_id':deviceId,'cursor':cursor},options:await _auth());
    return (r.data['acked_cursor'] as num).toInt();
  }

  @override
  Future<List<SyncDeviceView>> listDevices() async {
    final r=await _api.dio.get('/v1/sync/devices',options:await _auth());
    return (r.data['devices'] as List).map((e){
      final m=Map<String,dynamic>.from(e);
      return SyncDeviceView(
        deviceId:m['device_id'],name:m['name'],platform:m['platform'],appVersion:m['app_version'],
        ackedCursor:(m['acked_cursor'] as num).toInt(),active:m['active'] as bool,
        createdAt:DateTime.parse(m['created_at']).toUtc(),lastSeenAt:DateTime.parse(m['last_seen_at']).toUtc(),
        lastSyncAt:m['last_sync_at']==null?null:DateTime.parse(m['last_sync_at']).toUtc(),
      );
    }).toList(growable:false);
  }

  @override
  Future<void> revokeDevice(String deviceId) async {
    await _api.dio.delete('/v1/sync/devices/$deviceId',options:await _auth());
  }

  @override
  Future<List<PushOutcome>> push({required String deviceId, required List<CloudMutation> mutations}) async {
    final response = await _api.dio.post('/v1/sync/push', data: {
      'device_id': deviceId,
      'mutations': mutations.map((m) => {
        'mutation_id':m.id,'entity_type':m.entityType,'entity_id':m.entityId,'operation':m.operation,
        'payload':m.payload,'base_version':m.baseVersion,'client_modified_at':m.clientModifiedAt.toUtc().toIso8601String(),
      }).toList(),
    }, options: await _auth());
    final rows = (response.data['outcomes'] as List).cast<Map>();
    return rows.map((raw) {
      final m = Map<String,dynamic>.from(raw);
      return PushOutcome(
        mutationId:m['mutation_id'], disposition:m['disposition'], reason:m['reason'],
        record:_record(m['record']), canonical:_record(m['canonical']),
      );
    }).toList(growable:false);
  }

  @override
  Future<PullPage> bootstrap({required String deviceId}) async {
    final response = await _api.dio.get('/v1/sync/bootstrap', queryParameters:{'device_id':deviceId}, options: await _auth());
    return _page(response.data, forceHasMore:false);
  }

  @override
  Future<PullPage> pull({required String deviceId, required int cursor, int limit = 200}) async {
    final response = await _api.dio.get('/v1/sync/pull', queryParameters:{'device_id':deviceId,'cursor':cursor,'limit':limit}, options:await _auth());
    return _page(response.data);
  }

  PullPage _page(dynamic raw,{bool? forceHasMore}) {
    final m = Map<String,dynamic>.from(raw as Map);
    return PullPage(
      changes:(m['changes'] as List).map((e)=>_record(e)!).toList(growable:false),
      nextCursor:(m['next_cursor'] as num).toInt(),
      hasMore:forceHasMore ?? (m['has_more']==true),
      retainedFloor:(m['retained_floor'] as num?)?.toInt() ?? 0,
      resetRequired:m['reset_required']==true,
    );
  }

  CloudRecord? _record(dynamic raw) {
    if (raw == null) return null;
    final m=Map<String,dynamic>.from(raw as Map);
    return CloudRecord(
      entityType:m['entity_type'],entityId:m['entity_id'],version:(m['version'] as num).toInt(),
      payload:Map<String,Object?>.from(m['payload'] as Map),deleted:m['deleted'] as bool,
      updatedAt:DateTime.parse(m['updated_at']).toUtc(),serverSeq:(m['server_seq'] as num).toInt(),
    );
  }
}

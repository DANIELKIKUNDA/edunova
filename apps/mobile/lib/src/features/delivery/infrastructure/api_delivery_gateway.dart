import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../identity/application/identity_repository.dart';
import '../application/delivery_repository.dart';
import '../domain/delivery.dart';

class ApiDeliveryGateway implements DeliveryRemoteGateway {
  ApiDeliveryGateway({required ApiClient api,required IdentityRepository identity}):_api=api,_identity=identity;
  final ApiClient _api; final IdentityRepository _identity;

  Future<Map<String,String>> _auth() async{
    var s=await _identity.currentSession();
    if(s==null) return const {};
    if(s.accessExpired) s=await _identity.refresh();
    return {'Authorization':'Bearer ${s.accessToken}'};
  }

  @override
  Future<DeliveryGrantView> grant({required String resourceId,required String deliveryToken}) async{
    final r=await _api.dio.get('/v1/delivery/resources/$resourceId/grant',queryParameters:{'token':deliveryToken,'purpose':'offline'},options:Options(headers:await _auth()));
    final m=Map<String,dynamic>.from(r.data);
    return DeliveryGrantView(
      resourceId:m['resource_id'],url:m['url'],expiresAt:DateTime.parse(m['expires_at']).toUtc(),
      sizeBytes:(m['size_bytes'] as num).toInt(),supportsRange:m['supports_range']==true,requiresAppAuth:m['requires_app_auth']==true,
      checksumSha256:m['checksum_sha256']?.toString(),etag:m['etag']?.toString(),contentType:m['content_type']?.toString(),
    );
  }
}

import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../identity/application/identity_repository.dart';
import '../application/library_repository.dart';
import '../domain/library.dart';

class ApiLibraryGateway implements LibraryRemoteGateway {
  ApiLibraryGateway({required ApiClient api,required IdentityRepository identity}):_api=api,_identity=identity;
  final ApiClient _api; final IdentityRepository _identity;

  Future<Map<String,String>> _optionalAuthHeaders() async{
    var s=await _identity.currentSession(); if(s==null) return const {};
    if(s.accessExpired)s=await _identity.refresh(); return {'Authorization':'Bearer ${s.accessToken}'};
  }

  @override
  Future<LibraryCatalogPage> loadCatalogPage({String? facultyDomain,String? program,String? level,String? semester,String? cursor,String? ifNoneMatch,int limit=200}) async{
    final headers=await _optionalAuthHeaders();
    if(ifNoneMatch!=null) headers['If-None-Match']=ifNoneMatch;
    final r=await _api.dio.get('/v1/library/catalog',queryParameters:{
      if(facultyDomain!=null)'faculty_domain':facultyDomain,if(program!=null)'program':program,if(level!=null)'level':level,if(semester!=null)'semester':semester,
      if(cursor!=null)'cursor':cursor,'limit':limit,
    },options:Options(headers:headers,validateStatus:(s)=>s==200||s==304));
    if(r.statusCode==304){return LibraryCatalogPage(courses:const [],etag:ifNoneMatch??'',notModified:true);}
    final m=Map<String,dynamic>.from(r.data);
    return LibraryCatalogPage(
      courses:(m['courses'] as List).map((e)=>_course(Map<String,dynamic>.from(e))).toList(growable:false),
      nextCursor:m['next_cursor']?.toString(),etag:(m['etag']??r.headers.value('etag')??'').toString(),
    );
  }

  @override
  Future<LibraryManifest> loadManifest(String courseId) async{
    final headers=await _optionalAuthHeaders();
    final r=await _api.dio.get('/v1/library/courses/$courseId/manifest',options:Options(headers:headers));
    final m=Map<String,dynamic>.from(r.data); final c=_course(Map<String,dynamic>.from(m['course'])); final v=Map<String,dynamic>.from(m['version']);
    final version=LibraryVersionView(id:v['id'],courseId:c.id,label:v['label'],academicYear:v['academic_year'],sourceFingerprint:v['source_fingerprint'],changelog:v['changelog']??'',publishedAt:v['published_at']==null?null:DateTime.parse(v['published_at']).toUtc());
    final resources=(m['resources'] as List).map((e){final x=Map<String,dynamic>.from(e);return LibraryResourceView(id:x['id'],versionId:version.id,kind:x['kind'],title:x['title'],mimeType:x['mime_type'],sizeBytes:x['size_bytes'],checksumSha256:x['checksum_sha256'],premiumRequired:x['premium_required'],offlineAllowed:x['offline_allowed'],access:x['access'],deliveryToken:x['delivery_token']);}).toList(growable:false);
    return LibraryManifest(course:c,version:version,resources:resources,premium:m['premium']);
  }

  LibraryCourseView _course(Map<String,dynamic> m)=>LibraryCourseView(id:m['id'],facultyDomain:m['faculty_domain'],program:m['program'],level:m['level'],semester:m['semester'],title:m['title'],slug:m['slug'],description:m['description']??'',premiumRequired:m['premium_required']??false,activeVersionId:m['active_version_id'],updatedAt:DateTime.parse(m['updated_at']).toUtc());
}

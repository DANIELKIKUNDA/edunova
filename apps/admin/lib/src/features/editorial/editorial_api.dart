import 'dart:convert';
import 'package:http/http.dart' as http;
import 'studio_session.dart';

class StudioApiException implements Exception{
  final int statusCode; final String code;
  const StudioApiException(this.statusCode,this.code);
  bool get isConflict=>statusCode==409;
  @override String toString()=>code;
}

class EditorialApi{
  final String baseUrl;
  final StudioSessionStore sessionStore;
  String? _accessToken,_refreshToken;
  StudioSession? session;
  EditorialApi(this.baseUrl,{StudioSessionStore? sessionStore}):sessionStore=sessionStore??StudioSessionStore();
  factory EditorialApi.fromEnvironment()=>EditorialApi(const String.fromEnvironment('EDUNOVA_API_URL',defaultValue:'http://localhost:8000'));
  bool get isAuthenticated=>_accessToken!=null;
  String get displayName=>session?.displayName??'';

  Future<bool> restore()async{final s=await sessionStore.read();if(s==null)return false;_setSession(s,persist:false);try{await identityMe();return true;}catch(_){await clearSession();return false;}}
  Future<StudioSession> login(String login,String password)async{final r=await http.post(Uri.parse('$baseUrl/v1/identity/login'),headers:{'Content-Type':'application/json'},body:jsonEncode({'login':login.trim(),'password':password,'device_name':'EduNova Studio'}));final j=_decode(r);if(r.statusCode!=200)throw StudioApiException(r.statusCode,_detail(j));final s=StudioSession.fromJson(j as Map<String,dynamic>);_setSession(s);await sessionStore.save(s);try{await identityMe();}catch(e){await clearSession();rethrow;}return s;}
  Future<void> logout()async{final refresh=_refreshToken;try{if(refresh!=null)await http.post(Uri.parse('$baseUrl/v1/identity/logout'),headers:{'Content-Type':'application/json'},body:jsonEncode({'refresh_token':refresh}));}finally{await clearSession();}}
  Future<void> clearSession()async{_accessToken=null;_refreshToken=null;session=null;await sessionStore.clear();}
  void _setSession(StudioSession s,{bool persist=true}){session=s;_accessToken=s.accessToken;_refreshToken=s.refreshToken;}
  Future<bool> _refresh()async{final rt=_refreshToken;if(rt==null)return false;final r=await http.post(Uri.parse('$baseUrl/v1/identity/refresh'),headers:{'Content-Type':'application/json'},body:jsonEncode({'refresh_token':rt,'device_name':'EduNova Studio'}));if(r.statusCode!=200)return false;final j=_decode(r) as Map<String,dynamic>;final s=StudioSession.fromJson(j);_setSession(s);await sessionStore.save(s);return true;}

  Future<dynamic> _request(String method,String path,{Map<String,dynamic>? body,bool retry=true})async{
    final uri=Uri.parse('$baseUrl$path');
    final headers={'Content-Type':'application/json',if(_accessToken!=null)'Authorization':'Bearer $_accessToken'};
    late http.Response r;
    switch(method){case 'GET':r=await http.get(uri,headers:headers);break;case 'POST':r=await http.post(uri,headers:headers,body:body==null?null:jsonEncode(body));break;case 'PATCH':r=await http.patch(uri,headers:headers,body:jsonEncode(body??{}));break;case 'PUT':r=await http.put(uri,headers:headers,body:jsonEncode(body??{}));break;default:throw ArgumentError('method');}
    if(r.statusCode==401&&retry&&await _refresh())return _request(method,path,body:body,retry:false);
    final j=_decode(r);
    if(r.statusCode<200||r.statusCode>=300)throw StudioApiException(r.statusCode,_detail(j));
    return j;
  }
  dynamic _decode(http.Response r){if(r.body.isEmpty)return <String,dynamic>{};try{return jsonDecode(r.body);}catch(_){return {'detail':'invalid_server_response'};}}
  String _detail(dynamic j)=>j is Map<String,dynamic>?(j['detail']?.toString()??'request_failed'):'request_failed';

  Future<Map<String,dynamic>> identityMe()async=>(await _request('GET','/v1/identity/me')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> platformMe()async=>(await _request('GET','/v1/platform/me')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> platformInstitutionStatistics() async => (await _request('GET','/v1/platform/institutions/statistics')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> platformAuditEvents({int limit=25,int offset=0}) async => (await _request('GET','/v1/platform/audit/events?limit=$limit&offset=$offset')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> platformDashboard()async=>(await _request('GET','/v1/platform/dashboard')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> platformInstitutionDirectory({int limit=50,int offset=0,String? search,String? state}) async {
    final params=<String,String>{'limit':'$limit','offset':'$offset'};
    if(search!=null&&search.trim().isNotEmpty)params['search']=search.trim();
    if(state!=null&&state.isNotEmpty)params['state']=state;
    final url=Uri(path:'/v1/platform/institutions/directory',queryParameters:params).toString();
    return (await _request('GET',url)) as Map<String,dynamic>;
  }
  Future<List<dynamic>> platformInstitutionControls() async => (await _request('GET','/v1/platform/institutions/controls')) as List<dynamic>;
  Future<Map<String,dynamic>> changePlatformInstitutionControl(String id,String state,String reason,{int? expectedVersion}) async => (await _request('PUT','/v1/platform/institutions/${Uri.encodeComponent(id)}/control',body:{'state':state,'reason':reason,'expected_version':expectedVersion})) as Map<String,dynamic>;
  Future<List<dynamic>> platformMembers()async=>(await _request('GET','/v1/platform/members')) as List<dynamic>;
  Future<Map<String,dynamic>> grantPlatformMember(String accountId,String role,{int? expectedVersion})async=>(await _request('PUT','/v1/platform/members/${Uri.encodeComponent(accountId)}',body:{'role':role,if(expectedVersion!=null)'expected_version':expectedVersion})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> deactivatePlatformMember(String accountId,int expectedVersion)async=>(await _request('POST','/v1/platform/members/${Uri.encodeComponent(accountId)}/deactivate',body:{'expected_version':expectedVersion})) as Map<String,dynamic>;
  Future<List<dynamic>> platformInstitutionAdministrators(String id) async => (await _request('GET','/v1/platform/institutions/${Uri.encodeComponent(id)}/administrators')) as List<dynamic>;
  Future<Map<String,dynamic>> platformAssignAdministrator(String id,String account,String role,{int? expectedVersion}) async => (await _request('PUT','/v1/platform/institutions/${Uri.encodeComponent(id)}/administrators',body:{'account_id':account,'role':role,'expected_version':expectedVersion})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> platformRevokeAdministrator(String id,String account,int version) async => (await _request('POST','/v1/platform/institutions/${Uri.encodeComponent(id)}/administrators/${Uri.encodeComponent(account)}/revoke',body:{'expected_version':version})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> platformSupportTickets({int limit=25,int offset=0,String? state}) async => (await _request('GET',Uri(path:'/v1/platform/support/tickets',queryParameters:{'limit':'$limit','offset':'$offset',if(state!=null&&state.isNotEmpty)'state':state}).toString())) as Map<String,dynamic>;
  Future<Map<String,dynamic>> platformCreateSupportTicket(String institutionId,String title,String description,String priority) async => (await _request('POST','/v1/platform/support/tickets',body:{'institution_id':institutionId,'title':title,'description':description,'priority':priority})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> platformUpdateSupportTicket(String id,String state,int version,{String? assignedTo}) async => (await _request('PUT','/v1/platform/support/tickets/${Uri.encodeComponent(id)}',body:{'state':state,'assigned_to':assignedTo,'expected_version':version})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> me()async=>(await _request('GET','/v1/editorial/me')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> dashboard()async=>(await _request('GET','/v1/editorial/dashboard')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> searchItems({String? query,String? state,String? kind,String? risk,String? rights,int offset=0,int limit=50})async{
    final q=<String,String>{if(query!=null&&query.trim().isNotEmpty)'q':query.trim(),if(state!=null&&state.isNotEmpty)'state':state,if(kind!=null&&kind.isNotEmpty)'kind':kind,if(risk!=null&&risk.isNotEmpty)'risk':risk,if(rights!=null&&rights.isNotEmpty)'rights_status':rights,'offset':'$offset','limit':'$limit'};
    final uri=Uri(path:'/v1/editorial/items/search',queryParameters:q);return (await _request('GET',uri.toString())) as Map<String,dynamic>;
  }
  Future<Map<String,dynamic>> itemDetail(String id)async=>(await _request('GET','/v1/editorial/items/$id')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> createItem(Map<String,dynamic> body)async=>(await _request('POST','/v1/editorial/items',body:body)) as Map<String,dynamic>;
  Future<Map<String,dynamic>> updateItem(String id,Map<String,dynamic> body)async=>(await _request('PATCH','/v1/editorial/items/$id',body:body)) as Map<String,dynamic>;
  Future<Map<String,dynamic>> addRevision(String id,Map<String,dynamic> body)async=>(await _request('POST','/v1/editorial/items/$id/revisions',body:body)) as Map<String,dynamic>;
  Future<Map<String,dynamic>> restoreRevision(String id,String revisionId,Map<String,dynamic> body)async=>(await _request('POST','/v1/editorial/items/$id/revisions/$revisionId/restore',body:body)) as Map<String,dynamic>;
  Future<Map<String,dynamic>> submitReview(String id,int version)async=>(await _request('POST','/v1/editorial/items/$id/submit-review',body:{'expected_version':version})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> review(String id,Map<String,dynamic> body)async=>(await _request('POST','/v1/editorial/items/$id/review',body:body)) as Map<String,dynamic>;
  Future<Map<String,dynamic>> publish(String id,String changelog,int version)async=>(await _request('POST','/v1/editorial/items/$id/publish',body:{'changelog':changelog,'expected_version':version})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> archive(String id,int version)async=>(await _request('POST','/v1/editorial/items/$id/archive',body:{'expected_version':version})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> assign(String id,String assignee,String stage,String? dueAt)async=>(await _request('POST','/v1/editorial/items/$id/assignments',body:{'assignee_id':assignee,'stage':stage,if(dueAt!=null)'due_at':dueAt})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> verifySource(String sourceId)async=>(await _request('POST','/v1/editorial/sources/$sourceId/verify')) as Map<String,dynamic>;
  Future<List<dynamic>> members()async=>(await _request('GET','/v1/editorial/members')) as List<dynamic>;
  Future<Map<String,dynamic>> setMember(Map<String,dynamic> body)async=>(await _request('PUT','/v1/editorial/members',body:body)) as Map<String,dynamic>;
}

extension IngestionStudioApi on EditorialApi{
  Future<Map<String,dynamic>> ingestionDashboard()async=>(await _request('GET','/v1/ingestion/dashboard')) as Map<String,dynamic>;
  Future<List<dynamic>> ingestionBatches()async=>(await _request('GET','/v1/ingestion/batches?limit=100&offset=0')) as List<dynamic>;
  Future<Map<String,dynamic>> ingestionBatch(String id)async=>(await _request('GET','/v1/ingestion/batches/$id')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> createIngestionBatch(Map<String,dynamic> body)async=>(await _request('POST','/v1/ingestion/batches',body:body)) as Map<String,dynamic>;
  Future<Map<String,dynamic>> startIngestionBatch(String id,{int priority=50})async=>(await _request('POST','/v1/ingestion/batches/$id/start',body:{'priority':priority})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> retryIngestionJob(String id)async=>(await _request('POST','/v1/ingestion/jobs/$id/retry')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> ingestionPreview(String documentId,{int page=1})async=>(await _request('GET','/v1/ingestion/documents/$documentId/preview?page=$page')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> uploadImageBundle(String batchId,String bundleName,List<MapEntry<String,List<int>>> files,{String? idempotencyKey})async{
    Future<http.Response> send() async{
      final uri=Uri.parse('$baseUrl/v1/ingestion/batches/$batchId/image-bundles').replace(queryParameters:{'bundle_name':bundleName});
      final req=http.MultipartRequest('POST',uri);
      if(_accessToken!=null)req.headers['Authorization']='Bearer $_accessToken';
      req.headers['Idempotency-Key']=idempotencyKey??'bundle-${DateTime.now().microsecondsSinceEpoch}-${files.length}';
      for(final f in files){req.files.add(http.MultipartFile.fromBytes('files',f.value,filename:f.key));}
      final streamed=await req.send(); return http.Response.fromStream(streamed);
    }
    var r=await send(); if(r.statusCode==401&&await _refresh())r=await send();
    final j=_decode(r); if(r.statusCode<200||r.statusCode>=300)throw StudioApiException(r.statusCode,_detail(j)); return j as Map<String,dynamic>;
  }
  Future<Map<String,dynamic>> uploadIngestionFile(String batchId,String filename,List<int> bytes,String contentType,{String? idempotencyKey})async{
    Future<http.Response> send() async{
      final req=http.MultipartRequest('POST',Uri.parse('$baseUrl/v1/ingestion/batches/$batchId/files'));
      if(_accessToken!=null)req.headers['Authorization']='Bearer $_accessToken';
      req.headers['Idempotency-Key']=idempotencyKey??'studio-${DateTime.now().microsecondsSinceEpoch}-$filename-${bytes.length}';
      req.files.add(http.MultipartFile.fromBytes('file',bytes,filename:filename));
      final streamed=await req.send(); return http.Response.fromStream(streamed);
    }
    var r=await send();
    if(r.statusCode==401&&await _refresh())r=await send();
    final j=_decode(r); if(r.statusCode<200||r.statusCode>=300)throw StudioApiException(r.statusCode,_detail(j));
    return j as Map<String,dynamic>;
  }
}

extension ContentFactoryStudioApi on EditorialApi{
  Future<List<dynamic>> factoryRuns()async=>(await _request('GET','/v1/content-factory/runs?limit=100')) as List<dynamic>;
  Future<Map<String,dynamic>> factoryRun(String id)async=>(await _request('GET','/v1/content-factory/runs/$id')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> createFactoryRun(String documentId,{List<String>? assets})async=>(await _request('POST','/v1/content-factory/runs',body:{'document_id':documentId,if(assets!=null)'requested_assets':assets})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> processFactoryRun(String id)async=>(await _request('POST','/v1/content-factory/runs/$id/process')) as Map<String,dynamic>;
}


extension PublicationStudioApi on EditorialApi{
  Future<Map<String,dynamic>> publicationDashboard()async=>(await _request('GET','/v1/publication/dashboard')) as Map<String,dynamic>;
  Future<List<dynamic>> publicationReleases({String? state})async=>(await _request('GET','/v1/publication/releases${state==null?'':'?state=$state'}')) as List<dynamic>;
  Future<Map<String,dynamic>> publicationSnapshot(String id)async=>(await _request('GET','/v1/publication/releases/$id/snapshot')) as Map<String,dynamic>;
  Future<Map<String,dynamic>> publishRelease(String id,int version)async=>(await _request('POST','/v1/publication/releases/$id/publish',body:{'expected_version':version})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> withdrawRelease(String id,int version)async=>(await _request('POST','/v1/publication/releases/$id/withdraw',body:{'expected_version':version})) as Map<String,dynamic>;
  Future<Map<String,dynamic>> verifyPublicationSnapshot(String id)async=>(await _request('GET','/v1/publication/releases/$id/verify')) as Map<String,dynamic>;
}


extension QuestionFactoryStudioApi on EditorialApi{
 Future<Map<String,dynamic>> importQuestionPaper({required String format,required String content,required String bankId,required String courseId,required String sourceDocumentId})async=>(await _request('POST','/v1/assessment/question-factory/import',body:{'format':format,'content':content,'bank_id':bankId,'course_id':courseId,'source_document_id':sourceDocumentId})) as Map<String,dynamic>;
}

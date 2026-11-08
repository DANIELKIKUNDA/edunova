import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../../identity/application/identity_repository.dart';
import '../application/assistant_repository.dart';
import '../domain/assistant.dart';

class ApiAssistantGateway implements AssistantRemoteGateway {
  ApiAssistantGateway({required ApiClient api, required IdentityRepository identity}) : _api=api, _identity=identity;
  final ApiClient _api;
  final IdentityRepository _identity;

  Future<Options> _authOptions() async {
    var session=await _identity.currentSession();
    if (session==null) throw StateError('authentication_required');
    if (session.accessExpired) session=await _identity.refresh();
    return Options(headers:{'Authorization':'Bearer ${session.accessToken}'});
  }

  @override
  Future<AssistantRemoteAnswer> ask({required String question,required String task,required String privacyMode,String? courseId,String subjectDomain='general',List<Map<String,Object?>> localContext=const [],bool consentToRemoteAnalysis=false,List<Map<String,String>> conversationTurns=const [],String explanationDepth='standard'}) async {
    final r=await _api.dio.post('/v1/assistant/ask',options:await _authOptions(),data:{'question':question,'task':task,'privacy_mode':privacyMode,'course_id':courseId,'subject_domain':subjectDomain,'local_context':localContext,'consent_to_remote_analysis':consentToRemoteAnalysis,'language':'fr','conversation_turns':conversationTurns,'explanation_depth':explanationDepth});
    final m=Map<String,dynamic>.from(r.data);
    final citations=(m['citations'] as List).map((e){final c=Map<String,dynamic>.from(e);return AssistantCitation(chunkId:c['chunk_id'],documentId:c['document_id'],sectionTitle:c['section_title'],startPage:c['start_page'],endPage:c['end_page'],excerpt:c['excerpt']);}).toList();
    return AssistantRemoteAnswer(text:m['text'],citations:citations,grounded:m['grounded'],confidence:(m['confidence'] as num).toDouble(),abstained:m['abstained'],creditsCharged:m['credits_charged'],provider:m['provider'],model:m['model'],cacheHit:m['cache_hit'],safetyFlags:(m['safety_flags'] as List).cast<String>(),routeReason:m['route_reason'] as String?,groundingCoverage:((m['grounding_coverage'] ?? 0) as num).toDouble(),sourceCount:((m['source_count'] ?? 0) as num).toInt(),promptVersion:m['prompt_version'] as String?);
  }
}

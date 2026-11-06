import '../domain/assistant.dart';

abstract interface class AssistantLocalRepository {
  Stream<List<AssistantConversation>> watchConversations();
  Stream<List<AssistantMessage>> watchMessages(String conversationId);
  Future<void> saveConversation(AssistantConversation conversation);
  Future<void> saveMessage(AssistantMessage message);
  Future<List<AssistantMessage>> recentMessages(String conversationId, {int limit = 6});
  Future<void> deleteConversation(String conversationId);
}

abstract interface class AssistantRemoteGateway {
  Future<AssistantRemoteAnswer> ask({
    required String question,
    required String task,
    required String privacyMode,
    String? courseId,
    String subjectDomain = 'general',
    List<Map<String, Object?>> localContext = const [],
    bool consentToRemoteAnalysis = false,
    List<Map<String, String>> conversationTurns = const [],
    String explanationDepth = 'standard',
  });
}

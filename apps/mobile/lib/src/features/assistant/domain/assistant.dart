class AssistantCitation {
  const AssistantCitation({required this.chunkId, required this.documentId, required this.startPage, required this.endPage, required this.excerpt, this.sectionTitle});
  final String chunkId;
  final String documentId;
  final String? sectionTitle;
  final int startPage;
  final int endPage;
  final String excerpt;
}

class AssistantMessage {
  const AssistantMessage({required this.id, required this.conversationId, required this.role, required this.text, required this.createdAt, this.citations = const [], this.grounded = false, this.confidence = 0, this.creditsCharged = 0, this.provider, this.model, this.abstained = false, this.cacheHit = false, this.safetyFlags = const [], this.routeReason, this.groundingCoverage = 0, this.sourceCount = 0, this.promptVersion});
  final String id;
  final String conversationId;
  final String role;
  final String text;
  final DateTime createdAt;
  final List<AssistantCitation> citations;
  final bool grounded;
  final double confidence;
  final int creditsCharged;
  final String? provider;
  final String? model;
  final bool abstained;
  final bool cacheHit;
  final List<String> safetyFlags;
  final String? routeReason;
  final double groundingCoverage;
  final int sourceCount;
  final String? promptVersion;
}

class AssistantConversation {
  const AssistantConversation({required this.id, required this.title, required this.contextType, required this.subjectDomain, required this.createdAt, required this.updatedAt, this.contextId});
  final String id;
  final String title;
  final String contextType;
  final String? contextId;
  final String subjectDomain;
  final DateTime createdAt;
  final DateTime updatedAt;
}

class AssistantRemoteAnswer {
  const AssistantRemoteAnswer({required this.text, required this.citations, required this.grounded, required this.confidence, required this.abstained, required this.creditsCharged, this.provider, this.model, this.cacheHit = false, this.safetyFlags = const [], this.routeReason, this.groundingCoverage = 0, this.sourceCount = 0, this.promptVersion});
  final String text;
  final List<AssistantCitation> citations;
  final bool grounded;
  final double confidence;
  final bool abstained;
  final int creditsCharged;
  final String? provider;
  final String? model;
  final bool cacheHit;
  final List<String> safetyFlags;
  final String? routeReason;
  final double groundingCoverage;
  final int sourceCount;
  final String? promptVersion;
}

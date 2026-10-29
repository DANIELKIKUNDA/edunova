import '../../../core/security/local_account_access.dart';
import 'dart:convert';
import 'package:drift/drift.dart';

import '../../../core/database/app_database.dart';
import '../application/assistant_repository.dart';
import '../domain/assistant.dart';

class DriftAssistantRepository implements AssistantLocalRepository {
  final LocalAccountAccess _access = LocalAccountAccess();
  DriftAssistantRepository(this._db);
  final AppDatabase _db;

  @override
  Stream<List<AssistantConversation>> watchConversations() {
    final q = _db.select(_db.localAssistantConversations)
      ..orderBy([(t) => OrderingTerm.desc(t.updatedAt)]);
    return _access.protect(q.watch().map((rows) => rows.map((r) => AssistantConversation(
      id: r.id,
      title: r.title,
      contextType: r.contextType,
      contextId: r.contextId,
      subjectDomain: r.subjectDomain,
      createdAt: r.createdAt,
      updatedAt: r.updatedAt,
    )).toList(growable: false)));
  }

  @override
  Stream<List<AssistantMessage>> watchMessages(String conversationId) {
    final q = _db.select(_db.localAssistantMessages)
      ..where((t) => t.conversationId.equals(conversationId))
      ..orderBy([(t) => OrderingTerm.asc(t.createdAt)]);
    return _access.protect(q.watch().map((rows) => rows.map((r) {
      final decoded = jsonDecode(r.citationsJson);
      final raw = decoded is List ? decoded.whereType<Map>().map((m) => Map<String, dynamic>.from(m)).toList() : const <Map<String, dynamic>>[];
      final citations = raw.map((m) => AssistantCitation(
        chunkId: m['chunk_id'] as String,
        documentId: m['document_id'] as String,
        sectionTitle: m['section_title'] as String?,
        startPage: (m['start_page'] as num).toInt(),
        endPage: (m['end_page'] as num).toInt(),
        excerpt: m['excerpt'] as String,
      )).toList(growable: false);
      final safetyDecoded = jsonDecode(r.safetyFlagsJson);
      final safetyFlags = safetyDecoded is List ? safetyDecoded.whereType<String>().toList(growable: false) : const <String>[];
      return AssistantMessage(
        id: r.id,
        conversationId: r.conversationId,
        role: r.role,
        text: r.textContent,
        createdAt: r.createdAt,
        citations: citations,
        grounded: r.grounded,
        confidence: r.confidence,
        creditsCharged: r.creditsCharged,
        provider: r.provider,
        model: r.model,
        abstained: r.abstained,
        cacheHit: r.cacheHit,
        safetyFlags: safetyFlags,
        routeReason: r.routeReason,
        groundingCoverage: r.groundingCoverage,
        sourceCount: r.sourceCount,
        promptVersion: r.promptVersion,
      );
    }).toList(growable: false)));
  }

  @override
  Future<List<AssistantMessage>> recentMessages(String conversationId, {int limit = 6}) async {
    final q = _db.select(_db.localAssistantMessages)
      ..where((t) => t.conversationId.equals(conversationId) & (t.role.equals('user') | t.role.equals('assistant')))
      ..orderBy([(t) => OrderingTerm.desc(t.createdAt)])
      ..limit(limit);
    final rows = await q.get();
    return rows.reversed.map((r) => AssistantMessage(
      id: r.id, conversationId: r.conversationId, role: r.role, text: r.textContent, createdAt: r.createdAt,
      grounded: r.grounded, confidence: r.confidence, creditsCharged: r.creditsCharged, provider: r.provider, model: r.model,
      abstained: r.abstained, cacheHit: r.cacheHit, routeReason: r.routeReason, groundingCoverage: r.groundingCoverage,
      sourceCount: r.sourceCount, promptVersion: r.promptVersion,
    )).toList(growable: false);
  }

  @override
  Future<void> saveConversation(AssistantConversation c) async {
    await _access.assertOwned();
    await _db.into(_db.localAssistantConversations).insertOnConflictUpdate(LocalAssistantConversationsCompanion.insert(
      id: c.id,
      title: c.title,
      contextType: c.contextType,
      contextId: Value(c.contextId),
      subjectDomain: Value(c.subjectDomain),
      createdAt: c.createdAt,
      updatedAt: c.updatedAt,
    ));
  }

  @override
  Future<void> saveMessage(AssistantMessage m) async {
    await _access.assertOwned();
    final citations = jsonEncode(m.citations.map((c) => {
      'chunk_id': c.chunkId,
      'document_id': c.documentId,
      'section_title': c.sectionTitle,
      'start_page': c.startPage,
      'end_page': c.endPage,
      'excerpt': c.excerpt,
    }).toList());
    await _db.transaction(() async {
      await _db.into(_db.localAssistantMessages).insertOnConflictUpdate(LocalAssistantMessagesCompanion.insert(
        id: m.id,
        conversationId: m.conversationId,
        role: m.role,
        textContent: m.text,
        citationsJson: Value(citations),
        grounded: Value(m.grounded),
        confidence: Value(m.confidence),
        creditsCharged: Value(m.creditsCharged),
        provider: Value(m.provider),
        model: Value(m.model),
        abstained: Value(m.abstained),
        cacheHit: Value(m.cacheHit),
        safetyFlagsJson: Value(jsonEncode(m.safetyFlags)),
        routeReason: Value(m.routeReason),
        groundingCoverage: Value(m.groundingCoverage),
        sourceCount: Value(m.sourceCount),
        promptVersion: Value(m.promptVersion),
        createdAt: m.createdAt,
      ));
      await (_db.update(_db.localAssistantConversations)..where((t) => t.id.equals(m.conversationId))).write(
        LocalAssistantConversationsCompanion(updatedAt: Value(m.createdAt)),
      );
    });
  }

  @override
  Future<void> deleteConversation(String conversationId) async {
    await _access.assertOwned();
    await _db.transaction(() async {
      await (_db.delete(_db.localAssistantMessages)..where((t) => t.conversationId.equals(conversationId))).go();
      await (_db.delete(_db.localAssistantConversations)..where((t) => t.id.equals(conversationId))).go();
    });
  }
}

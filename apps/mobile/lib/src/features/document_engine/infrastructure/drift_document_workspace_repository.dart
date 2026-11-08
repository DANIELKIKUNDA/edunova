import '../../../core/security/local_account_access.dart';
import 'package:drift/drift.dart';

import '../../../core/database/app_database.dart';
import '../application/document_workspace_repository.dart';
import '../domain/document_workspace.dart';

class DriftDocumentWorkspaceRepository implements DocumentWorkspaceRepository {
  final LocalAccountAccess _access = LocalAccountAccess();
  DriftDocumentWorkspaceRepository(this._db);
  final AppDatabase _db;

  @override
  Stream<List<DocumentSection>> watchSections(String documentId) {
    final query = _db.select(_db.localDocumentSections)
      ..where((t) => t.documentId.equals(documentId))
      ..orderBy([(t) => OrderingTerm.asc(t.ordinal)]);
    return _access.protect(query.watch().map((rows) => rows
        .map((row) => DocumentSection(
              id: row.id,
              documentId: row.documentId,
              title: row.title,
              level: row.level,
              startPage: row.startPage,
              endPage: row.endPage,
              parentId: row.parentId,
              ordinal: row.ordinal,
            ))
        .toList(growable: false)));
  }

  @override
  Stream<List<DocumentAnnotation>> watchAnnotations(String documentId) {
    final query = _db.select(_db.localDocumentAnnotations)
      ..where((t) => t.documentId.equals(documentId))
      ..orderBy([(t) => OrderingTerm.desc(t.updatedAt)]);
    return _access.protect(query.watch().map((rows) => rows
        .map((row) => DocumentAnnotation(
              id: row.id,
              documentId: row.documentId,
              kind: DocumentAnnotationKind.values.byName(row.kind),
              pageNumber: row.pageNumber,
              excerpt: row.excerpt,
              note: row.note,
              anchorJson: row.anchorJson,
              createdAt: row.createdAt,
              updatedAt: row.updatedAt,
            ))
        .toList(growable: false)));
  }

  @override
  Stream<ReadingProgress?> watchProgress(String documentId) {
    final query = _db.select(_db.localReadingProgress)..where((t) => t.documentId.equals(documentId));
    return _access.protect(query.watchSingleOrNull().map((row) => row == null
        ? null
        : ReadingProgress(
            documentId: row.documentId,
            pageNumber: row.pageNumber,
            pageProgress: row.pageProgress,
            totalPages: row.totalPages,
            lastOpenedAt: row.lastOpenedAt,
            secondsSpent: row.secondsSpent,
          )));
  }

  @override
  Stream<DocumentAnalysisSummary?> watchAnalysis(String documentId) {
    final query = _db.select(_db.localDocumentAnalyses)..where((t) => t.documentId.equals(documentId));
    return _access.protect(query.watchSingleOrNull().map((row) => row == null
        ? null
        : DocumentAnalysisSummary(
            documentId: row.documentId,
            status: DocumentProcessingStatus.values.byName(row.status),
            pageCount: row.pageCount,
            nativeTextPages: row.nativeTextPages,
            ocrPages: row.ocrPages,
            textQuality: row.textQuality,
            lastError: row.lastError,
          )));
  }

  @override
  Future<void> saveAnnotation(DocumentAnnotation annotation) async {
    await _access.assertOwned();
    await _db.into(_db.localDocumentAnnotations).insertOnConflictUpdate(
          LocalDocumentAnnotationsCompanion.insert(
            id: annotation.id,
            documentId: annotation.documentId,
            kind: annotation.kind.name,
            pageNumber: annotation.pageNumber,
            excerpt: Value(annotation.excerpt),
            note: Value(annotation.note),
            anchorJson: Value(annotation.anchorJson),
            createdAt: annotation.createdAt,
            updatedAt: annotation.updatedAt,
          ),
        );
  }

  @override
  Future<void> deleteAnnotation(String annotationId) async {
    await _access.assertOwned();
    await (_db.delete(_db.localDocumentAnnotations)..where((t) => t.id.equals(annotationId))).go();
  }

  @override
  Future<void> saveProgress(ReadingProgress progress) async {
    await _access.assertOwned();
    await _db.into(_db.localReadingProgress).insertOnConflictUpdate(
          LocalReadingProgressCompanion.insert(
            documentId: progress.documentId,
            pageNumber: Value(progress.pageNumber),
            pageProgress: Value(progress.pageProgress),
            totalPages: Value(progress.totalPages),
            lastOpenedAt: progress.lastOpenedAt,
            secondsSpent: Value(progress.secondsSpent),
          ),
        );
  }


  @override
  Future<List<Map<String, Object?>>> loadTextChunks(String documentId, {int limit = 8}) async {
    final query = _db.select(_db.localDocumentTextChunks)
      ..where((t) => t.documentId.equals(documentId))
      ..orderBy([(t) => OrderingTerm.asc(t.ordinal)])
      ..limit(limit);
    final rows = await query.get();
    return rows.map((r) => <String, Object?>{
      'chunk_id': r.id, 'document_id': r.documentId, 'section_title': null,
      'start_page': r.startPage, 'end_page': r.endPage, 'text': r.textContent,
    }).toList(growable: false);
  }

  @override
  Future<List<Map<String, Object?>>> searchRelevantTextChunks(String documentId, String query, {int limit = 8}) async {
    final rows = await (_db.select(_db.localDocumentTextChunks)
      ..where((t) => t.documentId.equals(documentId))
      ..orderBy([(t) => OrderingTerm.asc(t.ordinal)])
      ..limit(240)).get();
    final terms = RegExp(r"[A-Za-zÀ-ÿ0-9_]{3,}")
        .allMatches(query.toLowerCase())
        .map((m) => m.group(0)!)
        .toSet();
    if (terms.isEmpty) return loadTextChunks(documentId, limit: limit);
    final scored = <({dynamic row, double score})>[];
    for (final row in rows) {
      final text = row.textContent.toLowerCase();
      var score = 0.0;
      for (final term in terms) {
        final count = RegExp(RegExp.escape(term)).allMatches(text).length;
        if (count > 0) score += 1.0 + (count.clamp(1, 4).toDouble() - 1.0) * .25;
      }
      if (score > 0) scored.add((row: row, score: score));
    }
    scored.sort((a, b) {
      final byScore = b.score.compareTo(a.score);
      if (byScore != 0) return byScore;
      return a.row.ordinal.compareTo(b.row.ordinal);
    });
    final selected = scored.take(limit).toList(growable: false);
    if (selected.isEmpty) return const [];
    final sectionIds = selected.map((item) => item.row.sectionId).whereType<String>().toSet();
    final sectionTitles = <String, String>{};
    if (sectionIds.isNotEmpty) {
      final sections = await (_db.select(_db.localDocumentSections)..where((t) => t.documentId.equals(documentId))).get();
      for (final section in sections) {
        if (sectionIds.contains(section.id)) sectionTitles[section.id] = section.title;
      }
    }
    return selected.map((item) {
      final r = item.row;
      return <String, Object?>{
        'chunk_id': r.id,
        'document_id': r.documentId,
        'section_title': r.sectionId == null ? null : sectionTitles[r.sectionId],
        'start_page': r.startPage,
        'end_page': r.endPage,
        'text': r.textContent,
      };
    }).toList(growable: false);
  }

}

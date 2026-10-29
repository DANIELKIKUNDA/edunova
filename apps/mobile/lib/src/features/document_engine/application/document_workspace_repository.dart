import '../domain/document_workspace.dart';

abstract interface class DocumentWorkspaceRepository {
  Stream<List<DocumentSection>> watchSections(String documentId);
  Stream<List<DocumentAnnotation>> watchAnnotations(String documentId);
  Stream<ReadingProgress?> watchProgress(String documentId);
  Stream<DocumentAnalysisSummary?> watchAnalysis(String documentId);
  Future<void> saveAnnotation(DocumentAnnotation annotation);
  Future<void> deleteAnnotation(String annotationId);
  Future<void> saveProgress(ReadingProgress progress);
  Future<List<Map<String, Object?>>> loadTextChunks(String documentId, {int limit = 8});
  Future<List<Map<String, Object?>>> searchRelevantTextChunks(String documentId, String query, {int limit = 8});
}

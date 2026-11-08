enum DocumentProcessingStatus { pending, extracting, ocr, structuring, ready, needsReview, failed }
enum DocumentAnnotationKind { bookmark, highlight, note, review }

class DocumentSection {
  const DocumentSection({
    required this.id,
    required this.documentId,
    required this.title,
    required this.level,
    required this.startPage,
    required this.endPage,
    required this.ordinal,
    this.parentId,
  });
  final String id;
  final String documentId;
  final String title;
  final int level;
  final int startPage;
  final int endPage;
  final int ordinal;
  final String? parentId;
}

class DocumentAnnotation {
  const DocumentAnnotation({
    required this.id,
    required this.documentId,
    required this.kind,
    required this.pageNumber,
    required this.createdAt,
    required this.updatedAt,
    this.excerpt,
    this.note,
    this.anchorJson,
  });
  final String id;
  final String documentId;
  final DocumentAnnotationKind kind;
  final int pageNumber;
  final String? excerpt;
  final String? note;
  final String? anchorJson;
  final DateTime createdAt;
  final DateTime updatedAt;
}

class ReadingProgress {
  const ReadingProgress({
    required this.documentId,
    required this.pageNumber,
    required this.pageProgress,
    required this.totalPages,
    required this.lastOpenedAt,
    required this.secondsSpent,
  });
  final String documentId;
  final int pageNumber;
  final double pageProgress;
  final int totalPages;
  final DateTime lastOpenedAt;
  final int secondsSpent;

  double get overallProgress => totalPages <= 0
      ? 0
      : ((pageNumber - 1 + pageProgress.clamp(0, 1)) / totalPages).clamp(0, 1);
}

class DocumentAnalysisSummary {
  const DocumentAnalysisSummary({
    required this.documentId,
    required this.status,
    required this.pageCount,
    required this.nativeTextPages,
    required this.ocrPages,
    required this.textQuality,
    this.lastError,
  });
  final String documentId;
  final DocumentProcessingStatus status;
  final int pageCount;
  final int nativeTextPages;
  final int ocrPages;
  final double textQuality;
  final String? lastError;
}

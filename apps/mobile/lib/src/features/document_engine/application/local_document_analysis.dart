import '../domain/document_workspace.dart';

enum DocumentPrivacyMode {
  /// Le document et son texte ne quittent jamais l'appareil.
  deviceOnly,

  /// L'utilisateur autorise explicitement l'envoi temporaire des extraits nécessaires.
  onlineAssist,
}

class DocumentAnalysisCapabilities {
  const DocumentAnalysisCapabilities({
    required this.pdfTextExtraction,
    required this.imageOcr,
    required this.scannedPdfOcr,
    required this.fullTextSearch,
    required this.outlineDetection,
  });
  final bool pdfTextExtraction;
  final bool imageOcr;
  final bool scannedPdfOcr;
  final bool fullTextSearch;
  final bool outlineDetection;
}

abstract interface class LocalDocumentAnalysisEngine {
  Future<DocumentAnalysisCapabilities> capabilities();
  Future<DocumentAnalysisSummary> analyze({
    required String documentId,
    required String localUri,
    required String mimeType,
    required DocumentPrivacyMode privacyMode,
  });
}

enum PersonalDocumentType {
  course,
  interrogation,
  exam,
  exercise,
  notes,
  other,
}

enum OcrStatus { notRequested, pending, completed, failed }

class PersonalDocument {
  const PersonalDocument({
    required this.id,
    required this.title,
    required this.originalFileName,
    required this.type,
    required this.localUri,
    required this.mimeType,
    required this.sizeBytes,
    required this.createdAt,
    required this.updatedAt,
    this.courseName,
    this.level,
    this.academicYear,
    this.isImage = false,
    this.ocrStatus = OcrStatus.notRequested,
  });

  final String id;
  final String title;
  final String originalFileName;
  final PersonalDocumentType type;
  final String localUri;
  final String mimeType;
  final int sizeBytes;
  final String? courseName;
  final String? level;
  final String? academicYear;
  final bool isImage;
  final OcrStatus ocrStatus;
  final DateTime createdAt;
  final DateTime updatedAt;
}

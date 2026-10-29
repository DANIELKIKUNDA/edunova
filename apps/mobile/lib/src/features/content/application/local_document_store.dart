import 'dart:typed_data';

class LocalDocumentCandidate {
  const LocalDocumentCandidate({
    required this.fileName,
    required this.mimeType,
    required this.sizeBytes,
    this.sourcePath,
    this.bytes,
  });

  final String fileName;
  final String mimeType;
  final int sizeBytes;
  final String? sourcePath;
  final Uint8List? bytes;
}

class StoredLocalDocument {
  const StoredLocalDocument({required this.uri, required this.sizeBytes});
  final String uri;
  final int sizeBytes;
}

abstract interface class LocalDocumentStore {
  Future<StoredLocalDocument> persist(String documentId, LocalDocumentCandidate candidate);
  Future<void> delete(String uri);
}

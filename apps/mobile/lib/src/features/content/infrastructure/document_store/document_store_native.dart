import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../../application/local_document_store.dart';

class NativePrivateDocumentStore implements LocalDocumentStore {
  @override
  Future<StoredLocalDocument> persist(String documentId, LocalDocumentCandidate candidate) async {
    final root = await getApplicationSupportDirectory();
    final directory = Directory(p.join(root.path, 'private_documents', documentId));
    await directory.create(recursive: true);
    final safeName = candidate.fileName.replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '_');
    final destination = File(p.join(directory.path, safeName));

    if (candidate.bytes != null) {
      await destination.writeAsBytes(candidate.bytes!, flush: true);
    } else if (candidate.sourcePath != null) {
      await File(candidate.sourcePath!).copy(destination.path);
    } else {
      throw ArgumentError('Le document ne contient ni bytes ni chemin source.');
    }

    final length = await destination.length();
    return StoredLocalDocument(uri: destination.path, sizeBytes: length);
  }

  @override
  Future<void> delete(String uri) async {
    final file = File(uri);
    if (await file.exists()) await file.delete();
  }
}

LocalDocumentStore createLocalDocumentStore() => NativePrivateDocumentStore();

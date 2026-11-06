import '../../application/local_document_store.dart';

/// LOT 1 pose explicitement le port Web. Le stockage binaire PWA sera branché
/// sur OPFS dans le lot Web/offline dédié afin d'éviter de faire transiter les
/// documents personnels par le backend.
class WebPrivateDocumentStore implements LocalDocumentStore {
  @override
  Future<StoredLocalDocument> persist(String documentId, LocalDocumentCandidate candidate) {
    throw UnsupportedError('Stockage OPFS PWA à brancher dans le lot Web/offline.');
  }

  @override
  Future<void> delete(String uri) async {}
}

LocalDocumentStore createLocalDocumentStore() => WebPrivateDocumentStore();

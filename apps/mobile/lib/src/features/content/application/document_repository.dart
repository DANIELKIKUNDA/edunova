import '../domain/personal_document.dart';

abstract interface class PersonalDocumentRepository {
  Future<void> save(PersonalDocument document);
  Future<PersonalDocument?> getById(String id);
  Stream<List<PersonalDocument>> watchAll();
  Future<void> delete(String id);
}

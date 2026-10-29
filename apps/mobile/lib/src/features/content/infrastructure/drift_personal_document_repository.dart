import 'package:drift/drift.dart';
import '../../../core/security/local_account_access.dart';

import '../../../core/database/app_database.dart';
import '../application/document_repository.dart';
import '../domain/personal_document.dart';

class DriftPersonalDocumentRepository implements PersonalDocumentRepository {
  DriftPersonalDocumentRepository(this._db);
  final AppDatabase _db;
  final LocalAccountAccess _access = LocalAccountAccess();

  @override
  Future<void> save(PersonalDocument document) async {
    await _access.assertOwned();
    await _db.into(_db.localPersonalDocuments).insertOnConflictUpdate(
      LocalPersonalDocumentsCompanion.insert(
        id: document.id,
        title: document.title,
        originalFileName: document.originalFileName,
        documentType: document.type.name,
        localUri: document.localUri,
        mimeType: document.mimeType,
        sizeBytes: document.sizeBytes,
        courseName: Value(document.courseName),
        level: Value(document.level),
        academicYear: Value(document.academicYear),
        isImage: Value(document.isImage),
        ocrStatus: Value(document.ocrStatus.name),
        createdAt: document.createdAt,
        updatedAt: document.updatedAt,
      ),
    );
  }

  @override
  Future<PersonalDocument?> getById(String id) async {
    await _access.assertOwned();
    final row = await (_db.select(_db.localPersonalDocuments)..where((t) => t.id.equals(id))).getSingleOrNull();
    return row == null ? null : _map(row);
  }

  @override
  Stream<List<PersonalDocument>> watchAll() {
    final query = _db.select(_db.localPersonalDocuments)
      ..orderBy([(t) => OrderingTerm.desc(t.updatedAt)]);
    return _access.protect(query.watch().map((rows) => rows.map(_map).toList(growable: false)));
  }

  @override
  Future<void> delete(String id) async {
    await _access.assertOwned();
    await (_db.delete(_db.localPersonalDocuments)..where((t) => t.id.equals(id))).go();
  }

  PersonalDocument _map(LocalPersonalDocument row) => PersonalDocument(
        id: row.id,
        title: row.title,
        originalFileName: row.originalFileName,
        type: PersonalDocumentType.values.byName(row.documentType),
        localUri: row.localUri,
        mimeType: row.mimeType,
        sizeBytes: row.sizeBytes,
        courseName: row.courseName,
        level: row.level,
        academicYear: row.academicYear,
        isImage: row.isImage,
        ocrStatus: OcrStatus.values.byName(row.ocrStatus),
        createdAt: row.createdAt,
        updatedAt: row.updatedAt,
      );
}

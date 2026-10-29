import 'dart:typed_data';

import 'package:edunova/src/features/content/application/document_repository.dart';
import 'package:edunova/src/features/content/application/import_personal_document.dart';
import 'package:edunova/src/features/content/application/local_document_store.dart';
import 'package:edunova/src/features/content/domain/personal_document.dart';
import 'package:edunova/src/features/sync/application/outbox_repository.dart';
import 'package:edunova/src/features/sync/domain/outbox_event.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('personal import persists metadata and queues outbox event', () async {
    final repo = _DocRepo();
    final outbox = _Outbox();
    final useCase = ImportPersonalDocument(repository: repo, store: _Store(), outbox: outbox);

    final result = await useCase(
      ImportPersonalDocumentCommand(
        candidate: LocalDocumentCandidate(
          fileName: 'chimie.pdf',
          mimeType: 'application/pdf',
          sizeBytes: 3,
          bytes: Uint8List.fromList([1, 2, 3]),
        ),
        title: 'Chimie générale',
        type: PersonalDocumentType.course,
      ),
    );

    expect(repo.value?.id, result.id);
    expect(outbox.events, hasLength(1));
    expect(outbox.events.single.eventType, 'personal_document.metadata.created');
  });
}

class _DocRepo implements PersonalDocumentRepository {
  PersonalDocument? value;
  @override Future<void> save(PersonalDocument document) async => value = document;
  @override Future<PersonalDocument?> getById(String id) async => value?.id == id ? value : null;
  @override Stream<List<PersonalDocument>> watchAll() => Stream.value(value == null ? [] : [value!]);
  @override Future<void> delete(String id) async => value = null;
}

class _Store implements LocalDocumentStore {
  @override
  Future<StoredLocalDocument> persist(String documentId, LocalDocumentCandidate candidate) async =>
      StoredLocalDocument(uri: '/private/$documentId/${candidate.fileName}', sizeBytes: candidate.sizeBytes);
  @override Future<void> delete(String uri) async {}
}

class _Outbox implements OutboxRepository {
  final events = <OutboxEvent>[];
  @override Future<void> enqueue(OutboxEvent event) async => events.add(event);
  @override Future<List<OutboxEvent>> pending({int limit = 50}) async => events.take(limit).toList();
  @override Future<void> markSent(String id) async {}
  @override Future<void> markFailed(String id) async {}
}

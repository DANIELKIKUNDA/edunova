import 'package:uuid/uuid.dart';

import '../../sync/application/outbox_repository.dart';
import '../../sync/domain/outbox_event.dart';
import '../domain/personal_document.dart';
import 'document_repository.dart';
import 'local_document_store.dart';

class ImportPersonalDocumentCommand {
  const ImportPersonalDocumentCommand({
    required this.candidate,
    required this.title,
    required this.type,
    this.courseName,
    this.level,
    this.academicYear,
  });

  final LocalDocumentCandidate candidate;
  final String title;
  final PersonalDocumentType type;
  final String? courseName;
  final String? level;
  final String? academicYear;
}

class ImportPersonalDocument {
  ImportPersonalDocument({
    required PersonalDocumentRepository repository,
    required LocalDocumentStore store,
    required OutboxRepository outbox,
  })  : _repository = repository,
        _store = store,
        _outbox = outbox;

  final PersonalDocumentRepository _repository;
  final LocalDocumentStore _store;
  final OutboxRepository _outbox;
  final Uuid _uuid = const Uuid();

  Future<PersonalDocument> call(ImportPersonalDocumentCommand command) async {
    final now = DateTime.now().toUtc();
    final id = _uuid.v4();
    final stored = await _store.persist(id, command.candidate);
    final isImage = command.candidate.mimeType.startsWith('image/');

    final document = PersonalDocument(
      id: id,
      title: command.title.trim(),
      originalFileName: command.candidate.fileName,
      type: command.type,
      localUri: stored.uri,
      mimeType: command.candidate.mimeType,
      sizeBytes: stored.sizeBytes,
      courseName: command.courseName?.trim().isEmpty == true ? null : command.courseName?.trim(),
      level: command.level?.trim().isEmpty == true ? null : command.level?.trim(),
      academicYear: command.academicYear?.trim().isEmpty == true ? null : command.academicYear?.trim(),
      isImage: isImage,
      createdAt: now,
      updatedAt: now,
    );

    await _repository.save(document);
    await _outbox.enqueue(
      OutboxEvent(
        id: _uuid.v4(),
        aggregateType: 'personal_document',
        aggregateId: id,
        eventType: 'personal_document.metadata.created',
        payloadJson: '{"id":"$id","type":"${document.type.name}","isImage":$isImage}',
        occurredAt: now,
      ),
    );
    return document;
  }
}

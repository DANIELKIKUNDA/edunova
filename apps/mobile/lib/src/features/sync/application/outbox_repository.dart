import '../domain/outbox_event.dart';

abstract interface class OutboxRepository {
  Future<void> enqueue(OutboxEvent event);
  Future<List<OutboxEvent>> pending({int limit = 50});
  Future<void> markSent(String id);
  Future<void> markFailed(String id);
}

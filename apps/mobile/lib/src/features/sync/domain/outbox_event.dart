enum OutboxStatus { pending, processing, sent, failed }

class OutboxEvent {
  const OutboxEvent({
    required this.id,
    required this.aggregateType,
    required this.aggregateId,
    required this.eventType,
    required this.payloadJson,
    required this.occurredAt,
    this.retryCount = 0,
    this.status = OutboxStatus.pending,
  });

  final String id;
  final String aggregateType;
  final String aggregateId;
  final String eventType;
  final String payloadJson;
  final DateTime occurredAt;
  final int retryCount;
  final OutboxStatus status;
}

enum AssessmentKind { interrogation, exam, assignment, practical, other }
enum AssessmentSource { edunova, personal }

class Assessment {
  const Assessment({
    required this.id,
    required this.courseId,
    required this.title,
    required this.kind,
    required this.source,
    required this.scheduledAt,
    this.localDocumentId,
  });

  final String id;
  final String courseId;
  final String title;
  final AssessmentKind kind;
  final AssessmentSource source;
  final DateTime scheduledAt;
  final String? localDocumentId;
}

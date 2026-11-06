enum CourseSource { edunova, personal }

class Course {
  const Course({
    required this.id,
    required this.title,
    required this.faculty,
    required this.program,
    required this.level,
    required this.semester,
    required this.source,
    required this.progress,
    required this.availableOffline,
    this.localDocumentId,
  });

  final String id;
  final String title;
  final String faculty;
  final String program;
  final String level;
  final String semester;
  final CourseSource source;
  final double progress;
  final bool availableOffline;
  final String? localDocumentId;
}

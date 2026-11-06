class AcademicProfile {
  const AcademicProfile({
    required this.id,
    required this.faculty,
    required this.program,
    required this.level,
    required this.semester,
    this.institution,
    required this.updatedAt,
  });

  final String id;
  final String faculty;
  final String program;
  final String level;
  final String semester;
  final String? institution;
  final DateTime updatedAt;
}

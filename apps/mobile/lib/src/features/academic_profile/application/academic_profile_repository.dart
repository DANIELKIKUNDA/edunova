import '../domain/academic_profile.dart';

abstract interface class AcademicProfileRepository {
  Future<AcademicProfile?> getActive();
  Future<void> save(AcademicProfile profile);
  Stream<AcademicProfile?> watchActive();
}

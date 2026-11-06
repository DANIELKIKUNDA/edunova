import 'package:drift/drift.dart';
import '../../../core/security/local_account_access.dart';

import '../../../core/database/app_database.dart';
import '../application/academic_profile_repository.dart';
import '../domain/academic_profile.dart';
import '../../sync/infrastructure/cloud_mutation_writer.dart';

class DriftAcademicProfileRepository implements AcademicProfileRepository {
  DriftAcademicProfileRepository(this._db,{required this.accountIdProvider});
  final AppDatabase _db;
  final LocalAccountAccess _access = LocalAccountAccess();
  final Future<String?> Function() accountIdProvider;

  @override
  Future<AcademicProfile?> getActive() async {
    await _access.assertOwned();
    final revision = _access.captureRevision();
    final row = await (_db.select(_db.localAcademicProfiles)..limit(1)).getSingleOrNull();
    await _access.assertUnchanged(revision);
    return row == null ? null : _map(row);
  }

  @override
  Future<void> save(AcademicProfile profile) async {
    await _access.assertOwned();
    final revision = _access.captureRevision();
    await _db.transaction(() async {
      await _db.into(_db.localAcademicProfiles).insertOnConflictUpdate(
        LocalAcademicProfilesCompanion.insert(
          id: profile.id,
          faculty: profile.faculty,
          program: profile.program,
          level: profile.level,
          semester: profile.semester,
          institution: Value(profile.institution),
          updatedAt: profile.updatedAt,
        ),
      );
      await CloudMutationWriter(db:_db,accountIdProvider:accountIdProvider).upsert('academic_profile', profile.id, {
        'faculty': profile.faculty,
        'program': profile.program,
        'level': profile.level,
        'semester': profile.semester,
        'institution': profile.institution,
      }, profile.updatedAt);
      await _access.assertUnchanged(revision);
    });
  }

  @override
  Stream<AcademicProfile?> watchActive() {
    return _access.protect((_db.select(_db.localAcademicProfiles)..limit(1)).watchSingleOrNull().map(
          (row) => row == null ? null : _map(row),
        ));
  }

  AcademicProfile _map(LocalAcademicProfile row) => AcademicProfile(
        id: row.id,
        faculty: row.faculty,
        program: row.program,
        level: row.level,
        semester: row.semester,
        institution: row.institution,
        updatedAt: row.updatedAt,
      );
}

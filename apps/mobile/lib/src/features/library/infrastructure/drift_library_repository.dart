import 'package:drift/drift.dart';
import '../../../core/security/local_account_access.dart';
import '../../identity/infrastructure/secure_session_store.dart';

import '../../../core/database/app_database.dart';
import '../application/library_repository.dart';
import '../domain/library.dart';
import '../../sync/infrastructure/cloud_mutation_writer.dart';

class DriftLibraryRepository implements LibraryLocalRepository {
  DriftLibraryRepository(this.db,{required this.accountIdProvider});
  final AppDatabase db;
  final LocalAccountAccess _access = LocalAccountAccess();
  final Future<String?> Function() accountIdProvider;

  @override
  Stream<List<LibraryCourseView>> watchCourses() async* {
    // Public catalog access must not depend on a private follows table.
    // A legacy ownerless installation may contain orphaned private rows;
    // never read those rows while browsing anonymously.
    await _access.assertReadable();
    final owner = await SecureSessionStore().ownerAccountId();
    final revision = _access.captureRevision();
    if (owner == null) {
      final publicQuery = db.select(db.localLibraryCourses)
        ..orderBy([
          (t) => OrderingTerm.asc(t.facultyDomain),
          (t) => OrderingTerm.asc(t.program),
          (t) => OrderingTerm.asc(t.level),
          (t) => OrderingTerm.asc(t.title),
        ]);
      await for (final courses in publicQuery.watch()) {
        await _access.assertUnchanged(revision);
        // A login during an anonymous stream requires a fresh subscription.
        if (await SecureSessionStore().ownerAccountId() != null) {
          throw StateError('local_session_changed_during_operation');
        }
        yield courses.map((course) => _course(course)).toList(growable: false);
      }
      return;
    }

    await _access.assertOwned();
    final joined = db.select(db.localLibraryCourses).join([
      leftOuterJoin(db.localLibraryCourseFollows,
          db.localLibraryCourseFollows.courseId.equalsExp(db.localLibraryCourses.id)),
    ])..orderBy([
      OrderingTerm.asc(db.localLibraryCourses.facultyDomain),
      OrderingTerm.asc(db.localLibraryCourses.program),
      OrderingTerm.asc(db.localLibraryCourses.level),
      OrderingTerm.asc(db.localLibraryCourses.title),
    ]);
    await for (final rows in joined.watch()) {
      await _access.assertUnchanged(revision, owned: true);
      yield rows.map((row) {
        final course = row.readTable(db.localLibraryCourses);
        final follow = row.readTableOrNull(db.localLibraryCourseFollows);
        return _course(course, followed: follow?.followed ?? false);
      }).toList(growable: false);
    }
  }

  Future<void> _upsertCourse(LibraryCourseView c) async {
    await db.into(db.localLibraryCourses).insertOnConflictUpdate(
          LocalLibraryCoursesCompanion.insert(
            id: c.id,
            facultyDomain: c.facultyDomain,
            program: c.program,
            level: c.level,
            semester: c.semester,
            title: c.title,
            slug: c.slug,
            description: Value(c.description),
            premiumRequired: Value(c.premiumRequired),
            activeVersionId: Value(c.activeVersionId),
            updatedAt: c.updatedAt,
          ),
        );
  }

  @override
  Future<String?> catalogEtag(String cacheKey) async {
    final row = await (db.select(db.localLibraryCatalogStates)
          ..where((t) => t.cacheKey.equals(cacheKey)))
        .getSingleOrNull();
    return row?.etag;
  }

  @override
  Future<void> replaceCatalogScope(
    List<LibraryCourseView> courses, {
    required String cacheKey,
    String? facultyDomain,
    String? program,
    String? level,
    String? semester,
    required String etag,
  }) async {
    final now = DateTime.now().toUtc();
    await db.transaction(() async {
      // Reconcile only the requested scope. A course that was unpublished or moved
      // disappears locally on the next successful complete refresh of this scope.
      final scope = db.select(db.localLibraryCourses);
      if (facultyDomain != null) scope.where((t) => t.facultyDomain.equals(facultyDomain));
      if (program != null) scope.where((t) => t.program.equals(program));
      if (level != null) scope.where((t) => t.level.equals(level));
      if (semester != null) scope.where((t) => t.semester.equals(semester));
      final existing = await scope.get();
      final incomingIds = courses.map((c) => c.id).toSet();
      for (final old in existing) {
        if (!incomingIds.contains(old.id)) {
          await (db.delete(db.localLibraryCourses)..where((t) => t.id.equals(old.id))).go();
        }
      }
      for (final course in courses) {
        await _upsertCourse(course);
      }
      await db.into(db.localLibraryCatalogStates).insertOnConflictUpdate(
            LocalLibraryCatalogStatesCompanion.insert(
              cacheKey: cacheKey,
              etag: Value(etag),
              nextCursor: const Value(null),
              lastRefreshAt: Value(now),
              updatedAt: now,
            ),
          );
    });
  }

  @override
  Future<void> saveManifest(LibraryManifest m) async {
    await db.transaction(() async {
      await _upsertCourse(m.course);
      final v = m.version;
      await db.into(db.localLibraryCourseVersions).insertOnConflictUpdate(
            LocalLibraryCourseVersionsCompanion.insert(
              id: v.id,
              courseId: v.courseId,
              label: v.label,
              academicYear: Value(v.academicYear),
              sourceFingerprint: v.sourceFingerprint,
              changelog: Value(v.changelog),
              publishedAt: Value(v.publishedAt),
            ),
          );
      // A manifest is authoritative for its version. Remove stale resources first.
      final current = await (db.select(db.localLibraryResources)
            ..where((t) => t.versionId.equals(v.id)))
          .get();
      final incoming = m.resources.map((r) => r.id).toSet();
      for (final old in current) {
        if (!incoming.contains(old.id)) {
          await (db.delete(db.localLibraryResources)..where((t) => t.id.equals(old.id))).go();
        }
      }
      for (final r in m.resources) {
        await db.into(db.localLibraryResources).insertOnConflictUpdate(
              LocalLibraryResourcesCompanion.insert(
                id: r.id,
                versionId: r.versionId,
                kind: r.kind,
                title: r.title,
                mimeType: Value(r.mimeType),
                sizeBytes: Value(r.sizeBytes),
                checksumSha256: Value(r.checksumSha256),
                premiumRequired: Value(r.premiumRequired),
                offlineAllowed: Value(r.offlineAllowed),
                access: Value(r.access),
                deliveryToken: Value(r.deliveryToken),
              ),
            );
      }
    });
  }

  @override
  Stream<List<LibraryResourceView>> watchResources(String versionId) {
    final q = db.select(db.localLibraryResources)
      ..where((t) => t.versionId.equals(versionId))
      ..orderBy([(t) => OrderingTerm.asc(t.kind), (t) => OrderingTerm.asc(t.title)]);
    return q.watch().map(
          (rows) => rows
              .map(
                (r) => LibraryResourceView(
                  id: r.id,
                  versionId: r.versionId,
                  kind: r.kind,
                  title: r.title,
                  mimeType: r.mimeType,
                  sizeBytes: r.sizeBytes,
                  checksumSha256: r.checksumSha256,
                  premiumRequired: r.premiumRequired,
                  offlineAllowed: r.offlineAllowed,
                  access: r.access,
                  deliveryToken: r.deliveryToken,
                ),
              )
              .toList(growable: false),
        );
  }

  @override
  Future<void> setCourseFollowed(String courseId,bool followed) async {
    await _access.assertOwned();
    final revision = _access.captureRevision();
    final now=DateTime.now().toUtc();
    await db.transaction(() async {
      await db.into(db.localLibraryCourseFollows).insertOnConflictUpdate(LocalLibraryCourseFollowsCompanion.insert(
        courseId:courseId,followed:Value(followed),updatedAt:now,
      ));
      await CloudMutationWriter(db:db,accountIdProvider:accountIdProvider).upsert(
        'course_follow',courseId,{'courseId':courseId,'followed':followed},now,
      );
      await _access.assertUnchanged(revision, owned: true);
    });
  }

  LibraryCourseView _course(LocalLibraryCourse r,{bool followed=false}) => LibraryCourseView(
        id: r.id,
        facultyDomain: r.facultyDomain,
        program: r.program,
        level: r.level,
        semester: r.semester,
        title: r.title,
        slug: r.slug,
        description: r.description,
        premiumRequired: r.premiumRequired,
        activeVersionId: r.activeVersionId,
        updatedAt: r.updatedAt,
        followed: followed,
      );
}

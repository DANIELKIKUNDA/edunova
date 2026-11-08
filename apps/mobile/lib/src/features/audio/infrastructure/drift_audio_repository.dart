import 'package:drift/drift.dart';

import '../../../core/database/app_database.dart';
import '../../../core/security/local_account_access.dart';
import '../application/audio_repository.dart';
import '../domain/audio.dart';

/// Playback positions and bookmarks are private student projections.
/// All reads and writes require the installation's authenticated owner.
class DriftAudioRepository implements AudioRepository {
  DriftAudioRepository(this.db);

  final AppDatabase db;
  final LocalAccountAccess _access = LocalAccountAccess();

  @override
  Stream<AudioPlaybackState?> watchPlayback(String id) => _access.protect(
        (db.select(db.localAudioPlaybackStates)..where((t) => t.id.equals(id)))
            .watchSingleOrNull()
            .map((r) => r == null
                ? null
                : AudioPlaybackState(
                    id: r.id,
                    courseId: r.courseId,
                    title: r.title,
                    summaryId: r.summaryId,
                    characterOffset: r.characterOffset,
                    speechRate: r.speechRate,
                    completed: r.completed,
                    lastPlayedAt: r.lastPlayedAt,
                  )),
        owned: true,
      );

  @override
  Future<void> savePlayback(AudioPlaybackState v) async {
    await _access.assertOwned();
    final revision = _access.captureRevision();
    await db.transaction(() async {
      await db.into(db.localAudioPlaybackStates).insertOnConflictUpdate(
            LocalAudioPlaybackStatesCompanion.insert(
              id: v.id,
              courseId: v.courseId,
              summaryId: Value(v.summaryId),
              title: v.title,
              characterOffset: Value(v.characterOffset),
              speechRate: Value(v.speechRate),
              completed: Value(v.completed),
              lastPlayedAt: Value(v.lastPlayedAt),
              updatedAt: DateTime.now(),
            ),
          );
      // Throwing here rolls back the transaction on logout/account changes.
      await _access.assertUnchanged(revision, owned: true);
    });
  }

  @override
  Stream<List<AudioBookmark>> watchBookmarks(String playbackId) =>
      _access.protect(
        (db.select(db.localAudioBookmarks)
              ..where((t) => t.playbackId.equals(playbackId))
              ..orderBy([(t) => OrderingTerm.asc(t.characterOffset)]))
            .watch()
            .map((rows) => rows
                .map((r) => AudioBookmark(
                      id: r.id,
                      playbackId: r.playbackId,
                      characterOffset: r.characterOffset,
                      label: r.label,
                      createdAt: r.createdAt,
                    ))
                .toList()),
        owned: true,
      );

  @override
  Future<void> addBookmark(AudioBookmark v) async {
    await _access.assertOwned();
    final revision = _access.captureRevision();
    await db.transaction(() async {
      await db.into(db.localAudioBookmarks).insert(
            LocalAudioBookmarksCompanion.insert(
              id: v.id,
              playbackId: v.playbackId,
              characterOffset: v.characterOffset,
              label: Value(v.label),
              createdAt: v.createdAt,
            ),
          );
      await _access.assertUnchanged(revision, owned: true);
    });
  }
}

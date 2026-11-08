import '../domain/audio.dart';
abstract class AudioRepository {
  Stream<AudioPlaybackState?> watchPlayback(String id);
  Future<void> savePlayback(AudioPlaybackState value);
  Stream<List<AudioBookmark>> watchBookmarks(String playbackId);
  Future<void> addBookmark(AudioBookmark value);
}

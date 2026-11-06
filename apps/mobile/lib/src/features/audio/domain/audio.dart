class AudioPlaybackState {
  const AudioPlaybackState({required this.id,required this.courseId,required this.title,this.summaryId,this.characterOffset=0,this.speechRate=1.0,this.completed=false,this.lastPlayedAt});
  final String id; final String courseId; final String? summaryId; final String title; final int characterOffset; final double speechRate; final bool completed; final DateTime? lastPlayedAt;
}
class AudioBookmark {
  const AudioBookmark({required this.id,required this.playbackId,required this.characterOffset,this.label,required this.createdAt});
  final String id; final String playbackId; final int characterOffset; final String? label; final DateTime createdAt;
}

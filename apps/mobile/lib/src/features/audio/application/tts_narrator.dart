abstract class TtsNarrator {
  Future<void> initialize();
  Future<void> speak(String text,{int startOffset=0,double rate=1.0,void Function(int start,int end)? onProgress,void Function()? onComplete});
  Future<void> pause();
  Future<void> stop();
}

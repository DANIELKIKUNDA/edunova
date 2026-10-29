import 'package:flutter_tts/flutter_tts.dart';
import '../application/tts_narrator.dart';
class DeviceTtsNarrator implements TtsNarrator {
  final FlutterTts _tts=FlutterTts(); bool _ready=false;
  @override Future<void> initialize() async {if(_ready)return; await _tts.setLanguage('fr-FR'); await _tts.awaitSpeakCompletion(false); _ready=true;}
  @override Future<void> speak(String text,{int startOffset=0,double rate=1.0,void Function(int start,int end)? onProgress,void Function()? onComplete}) async {
    await initialize(); await _tts.stop(); await _tts.setSpeechRate(rate.clamp(.5,2.0).toDouble());
    if(onProgress!=null){_tts.setProgressHandler((_,start,end,word)=>onProgress(startOffset+start,startOffset+end));}
    if(onComplete!=null){_tts.setCompletionHandler(onComplete);}
    final safe=startOffset.clamp(0,text.length); await _tts.speak(text.substring(safe));
  }
  @override Future<void> pause() async {await _tts.pause();}
  @override Future<void> stop() async {await _tts.stop();}
}

import '../domain/study_plan.dart';

class ParsedTimetableRow {
  const ParsedTimetableRow({required this.weekday, required this.startMinute, required this.endMinute, required this.title, required this.confidence});
  final int weekday;
  final int startMinute;
  final int endMinute;
  final String title;
  final double confidence;

  TimetableEntry toEntry(String id) => TimetableEntry(id:id,title:title,weekday:weekday,startMinute:startMinute,endMinute:endMinute);
}

class ScheduleTextParser {
  const ScheduleTextParser();
  static const _days = {
    'lundi':1,'lun':1,'mardi':2,'mar':2,'mercredi':3,'mer':3,
    'jeudi':4,'jeu':4,'vendredi':5,'ven':5,'samedi':6,'sam':6,'dimanche':7,'dim':7,
  };
  static final _line = RegExp(r'^\s*([A-Za-zÀ-ÿ]+)\s+(\d{1,2})[:hH](\d{2})\s*[-–—]\s*(\d{1,2})[:hH](\d{2})\s+(.+?)\s*$');

  List<ParsedTimetableRow> parse(String text) {
    final result=<ParsedTimetableRow>[];
    for(final raw in text.split('\n')){
      final m=_line.firstMatch(raw);
      if(m==null) continue;
      final day=_days[_normalize(m.group(1)!)];
      if(day==null) continue;
      final h1=int.parse(m.group(2)!); final min1=int.parse(m.group(3)!);
      final h2=int.parse(m.group(4)!); final min2=int.parse(m.group(5)!);
      final start=h1*60+min1; final end=h2*60+min2; final title=m.group(6)!.trim();
      if(start<0||end>1440||end<=start||title.isEmpty) continue;
      result.add(ParsedTimetableRow(weekday:day,startMinute:start,endMinute:end,title:title,confidence:.95));
    }
    return result;
  }

  String _normalize(String value) => value.toLowerCase()
      .replaceAll(RegExp('[àáâä]'),'a').replaceAll(RegExp('[éèêë]'),'e')
      .replaceAll(RegExp('[îï]'),'i').replaceAll(RegExp('[ôö]'),'o')
      .replaceAll(RegExp('[ùûü]'),'u').replaceAll('ç','c');
}

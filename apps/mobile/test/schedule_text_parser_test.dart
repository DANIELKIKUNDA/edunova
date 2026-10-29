import 'package:edunova/src/features/study_plan/application/schedule_text_parser.dart';
import 'package:flutter_test/flutter_test.dart';

void main(){
  test('parses French OCR timetable rows conservatively',(){
    final rows=const ScheduleTextParser().parse('Lundi 08:00-10:00 Anatomie\nMercredi 14h30–16h00 Chimie');
    expect(rows.length,2);
    expect(rows.first.weekday,1);
    expect(rows.first.startMinute,480);
    expect(rows.last.title,'Chimie');
  });
}

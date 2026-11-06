import 'package:edunova/src/features/study_plan/domain/study_plan.dart';
import 'package:flutter_test/flutter_test.dart';

void main(){
  test('planning engine prioritizes imminent weak course and respects budget',(){
    final now=DateTime(2026,9,20,10);
    final plan=const PlanningEngine().build(
      now:now,budgetMinutes:15,
      snapshots:const [
        CoursePlanningSnapshot(courseId:'bio',title:'Bio',readiness:30,openErrors:5,hasQuiz:true),
        CoursePlanningSnapshot(courseId:'math',title:'Math',readiness:85,hasQuiz:true),
      ],
      events:[AcademicEvent(id:'e',courseId:'bio',title:'Interro',kind:AcademicEventKind.interrogation,startsAt:DateTime(2026,9,22,10))],
      tomorrowCourseIds:const {},
    );
    expect(plan, isNotEmpty);
    expect(plan.first.courseId,'bio');
    expect(plan.fold<int>(0,(sum,row)=>sum+row.minutes),lessThanOrEqualTo(15));
  });

  test('emergency plan consumes requested budget',(){
    final event=AcademicEvent(id:'e',courseId:'bio',title:'Interro',kind:AcademicEventKind.interrogation,startsAt:DateTime(2026,9,21,8));
    final plan=const PlanningEngine().emergency(event:event,state:const CoursePlanningSnapshot(courseId:'bio',title:'Bio',readiness:40,openErrors:4),budgetMinutes:60);
    expect(plan.fold<int>(0,(sum,row)=>sum+row.minutes),60);
  });
}

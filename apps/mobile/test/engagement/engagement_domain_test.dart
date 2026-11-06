import 'package:flutter_test/flutter_test.dart';
import 'package:edunova/src/features/engagement/domain/engagement.dart';

void main(){
  test('preferences copyWith preserves untouched values',(){
    const p=EngagementPreferences(maxDailyNotifications:2,dailyGoalMinutes:30);
    final q=p.copyWith(dailyGoalMinutes:45);
    expect(q.maxDailyNotifications,2); expect(q.dailyGoalMinutes,45);
  });
  test('notification model keeps priority and expiry',(){
    final now=DateTime.utc(2026,9,21,8);
    final n=LocalNotificationView(id:'1',eventId:'e',dedupeKey:'x',fireAt:now,expiresAt:now.add(const Duration(hours:2)),title:'t',body:'b',category:'assessment',status:'planned',priority:90);
    expect(n.priority,90); expect(n.expiresAt!.isAfter(n.fireAt),isTrue);
  });
}

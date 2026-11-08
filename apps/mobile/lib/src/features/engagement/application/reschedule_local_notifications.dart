import '../domain/engagement.dart';
import 'engagement_repository.dart';
import 'local_notification_scheduler.dart';

class RescheduleLocalNotifications {
  const RescheduleLocalNotifications(this.repository,this.scheduler);
  final EngagementRepository repository; final LocalNotificationScheduler scheduler;

  bool _enabled(String category, EngagementPreferences p) => switch(category){
    'assessment' => p.assessmentEnabled,
    'study_plan' => p.studyPlanEnabled,
    'flashcards' => p.flashcardsEnabled,
    'streak' => p.streakEnabled,
    'content' => p.contentEnabled,
    _ => true,
  };

  DateTime _shiftQuiet(DateTime fireAt, EngagementPreferences p){
    final local=fireAt.toLocal(); final minute=local.hour*60+local.minute; final start=p.quietStartMinute,end=p.quietEndMinute;
    final quiet=start==end?false:(start<end?minute>=start&&minute<end:minute>=start||minute<end);
    if(!quiet)return fireAt;
    var day=DateTime(local.year,local.month,local.day); if(start>end&&minute>=start)day=day.add(const Duration(days:1));
    return DateTime(day.year,day.month,day.day,end~/60,end%60).toUtc();
  }

  Future<void> run() async {
    await scheduler.initialize(); await scheduler.cancelAll();
    final prefs=await repository.loadPreferences(); if(prefs.maxDailyNotifications<=0)return;
    final now=DateTime.now(); final raw=await repository.watchUpcomingNotifications(limit:64).first;
    final dedupe=<String>{}; final byDay=<String,List<LocalNotificationView>>{};
    for(final n in raw){
      if(!_enabled(n.category,prefs))continue; if(n.expiresAt!=null&&!n.expiresAt!.isAfter(now))continue;
      final key=n.dedupeKey??n.id; if(!dedupe.add(key))continue; final shifted=_shiftQuiet(n.fireAt,prefs);
      if(n.expiresAt!=null&&shifted.isAfter(n.expiresAt!))continue;
      final adjusted=LocalNotificationView(id:n.id,eventId:n.eventId,dedupeKey:n.dedupeKey,fireAt:shifted,expiresAt:n.expiresAt,title:n.title,body:n.body,category:n.category,status:n.status,deepLink:n.deepLink,priority:n.priority);
      final local=shifted.toLocal(); final day='${local.year}-${local.month.toString().padLeft(2,'0')}-${local.day.toString().padLeft(2,'0')}';
      byDay.putIfAbsent(day,()=>[]).add(adjusted);
    }
    for(final items in byDay.values){
      items.sort((a,b){final p=b.priority.compareTo(a.priority);return p!=0?p:a.fireAt.compareTo(b.fireAt);});
      for(final item in items.take(prefs.maxDailyNotifications)){await scheduler.schedule(item);}
    }
  }
}

import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../identity/application/identity_repository.dart';
import '../domain/engagement.dart';

class ApiEngagementGateway {
  ApiEngagementGateway({required ApiClient api,required IdentityRepository identity}):_api=api,_identity=identity;
  final ApiClient _api; final IdentityRepository _identity;
  Future<Map<String,String>> _headers() async {var s=await _identity.currentSession(); if(s==null) throw StateError('authentication_required'); if(s.accessExpired)s=await _identity.refresh(); return {'Authorization':'Bearer ${s.accessToken}'};}
  Future<void> syncPreferences(EngagementPreferences p) async {
    await _api.dio.put('/v1/engagement/preferences',options:Options(headers:await _headers()),data:{'quiet_start_minute':p.quietStartMinute,'quiet_end_minute':p.quietEndMinute,'max_daily_notifications':p.maxDailyNotifications,'preferred_study_minute':p.preferredStudyMinute,'assessment_enabled':p.assessmentEnabled,'study_plan_enabled':p.studyPlanEnabled,'flashcards_enabled':p.flashcardsEnabled,'streak_enabled':p.streakEnabled,'content_enabled':p.contentEnabled,'push_enabled':p.pushEnabled,'timezone_offset_minutes':p.timezoneOffsetMinutes,'daily_goal_minutes':p.dailyGoalMinutes});
  }
  Future<void> syncDay(EngagementDailyStat d) async {await _api.dio.post('/v1/engagement/activity',options:Options(headers:await _headers()),data:{'day_key':d.dayKey,'active_minutes':d.activeMinutes,'completed_tasks':d.completedTasks,'quiz_questions':d.quizQuestions,'flashcards_reviewed':d.flashcardsReviewed});}

  Future<void> registerPushDevice({required String deviceId,required String platform,required String token}) async {
    await _api.dio.post('/v1/engagement/push-devices',options:Options(headers:await _headers()),data:{'device_id':deviceId,'platform':platform,'token':token});
  }
  Future<void> revokePushDevice(String deviceId) async {
    await _api.dio.delete('/v1/engagement/push-devices/$deviceId',options:Options(headers:await _headers()));
  }
}

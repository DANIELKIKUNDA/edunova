import '../domain/adaptive_planning.dart';

class AvailabilityRule {
  const AvailabilityRule({
    required this.id,
    required this.weekday,
    required this.startMinute,
    required this.endMinute,
    this.energy = EnergyLevel.medium,
    this.isActive = true,
  });
  final String id;
  final int weekday;
  final int startMinute;
  final int endMinute;
  final EnergyLevel energy;
  final bool isActive;
}

class PlanningPreferences {
  const PlanningPreferences({
    this.dailyBudgetMinutes = 30,
    this.maxNotificationsPerDay = 2,
    this.quietStartMinute = 1320,
    this.quietEndMinute = 420,
    this.maxContinuousMinutes = 50,
    this.breakMinutes = 10,
    this.maxCoursesPerDay = 4,
    this.maxCourseSwitches = 5,
    this.targetReadiness = 80,
    this.planningHorizonDays = 14,
  });
  final int dailyBudgetMinutes;
  final int maxNotificationsPerDay;
  final int quietStartMinute;
  final int quietEndMinute;
  final int maxContinuousMinutes;
  final int breakMinutes;
  final int maxCoursesPerDay;
  final int maxCourseSwitches;
  final int targetReadiness;
  final int planningHorizonDays;
}


class PlanningDebt {
  const PlanningDebt({required this.courseId, this.overdueMinutes = 0, this.deferredCount = 0});
  final String courseId;
  final int overdueMinutes;
  final int deferredCount;
}

abstract interface class AdaptivePlanningRepository {
  Stream<List<AvailabilityRule>> watchAvailabilityRules();
  Stream<List<AdaptivePlanBlock>> watchTodayBlocks();
  Future<PlanningPreferences> loadPreferences();
  Future<Map<String, PlanningDebt>> loadDebts();
  Future<void> savePreferences(PlanningPreferences value);
  Future<void> saveAvailabilityRule(AvailabilityRule value);
  Future<void> deleteAvailabilityRule(String id);
  Future<void> replaceTodayBlocks(List<AdaptivePlanBlock> blocks, DateTime generatedAt, {required String reason});
  Future<void> completeBlock(String blockId, {required int actualMinutes});
  Future<void> deferBlock(String blockId, {int days = 1});
  Future<void> setPinned(String blockId, bool value);
}

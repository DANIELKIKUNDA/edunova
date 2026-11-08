import '../../features/commerce/domain/combined_access.dart';
import '../../features/campus_services/infrastructure/campus_services_gateway.dart';
import '../../features/campus_intelligence/infrastructure/campus_intelligence_gateway.dart';
import '../../features/analytics/application/analytics_engine.dart';
import '../../features/analytics/application/analytics_repository.dart';
import '../../features/analytics/domain/analytics.dart';
import '../../features/analytics/infrastructure/drift_analytics_repository.dart';
import '../../features/engagement/application/engagement_repository.dart';
import '../../features/engagement/application/reschedule_local_notifications.dart';
import '../../features/engagement/domain/engagement.dart';
import '../../features/engagement/infrastructure/api_engagement_gateway.dart';
import '../../features/engagement/infrastructure/drift_engagement_repository.dart';
import '../../features/engagement/infrastructure/local_notification_scheduler.dart';
import '../../features/engagement/infrastructure/remote_push_registrar.dart';
import '../../features/audio/application/audio_repository.dart';
import '../../features/audio/domain/audio.dart';
import '../../features/audio/application/tts_narrator.dart';
import '../../features/audio/infrastructure/drift_audio_repository.dart';
import '../../features/audio/infrastructure/device_tts_narrator.dart';
import '../../features/delivery/application/delivery_repository.dart';
import '../../features/delivery/application/download_resource.dart';
import '../../features/delivery/domain/delivery.dart';
import '../../features/delivery/infrastructure/api_delivery_gateway.dart';
import '../../features/delivery/infrastructure/drift_offline_delivery_repository.dart';
import '../../features/delivery/infrastructure/offline_resource_store.dart';
import 'package:flutter/foundation.dart';
import '../../features/sync/application/cloud_sync_repository.dart';
import '../../features/sync/application/run_cloud_sync.dart';
import '../../features/sync/domain/cloud_sync.dart';
import '../../features/sync/infrastructure/api_sync_gateway.dart';
import '../../features/sync/infrastructure/drift_cloud_sync_repository.dart';
import '../../features/library/application/library_repository.dart';
import '../../features/library/domain/library.dart';
import '../../features/library/infrastructure/api_library_gateway.dart';
import '../../features/library/infrastructure/drift_library_repository.dart';
import '../../features/assistant/application/assistant_repository.dart';
import '../../features/assistant/infrastructure/api_assistant_gateway.dart';
import '../../features/assistant/infrastructure/drift_assistant_repository.dart';
import '../../features/assistant/domain/assistant.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../network/api_client.dart';
import '../../features/identity/application/identity_repository.dart';
import '../../features/identity/application/session_store.dart';
import '../../features/identity/domain/auth_session.dart';
import '../../features/identity/infrastructure/api_identity_repository.dart';
import '../../features/identity/infrastructure/secure_session_store.dart';
import '../../features/commerce/application/commerce_repository.dart';
import '../../features/commerce/application/sync_entitlement.dart';
import '../../features/commerce/domain/commerce.dart';
import '../../features/commerce/infrastructure/api_commerce_gateway.dart';
import '../../features/commerce/infrastructure/drift_commerce_repository.dart';

import '../../features/academic_profile/application/academic_profile_repository.dart';
import '../../features/academic_profile/infrastructure/drift_academic_profile_repository.dart';
import '../../features/content/application/document_repository.dart';
import '../../features/content/application/import_personal_document.dart';
import '../../features/content/application/local_document_store.dart';
import '../../features/content/domain/personal_document.dart';
import '../../features/content/infrastructure/document_store/document_store.dart';
import '../../features/content/infrastructure/drift_personal_document_repository.dart';
import '../../features/document_engine/application/document_workspace_repository.dart';
import '../../features/document_engine/domain/document_workspace.dart';
import '../../features/document_engine/infrastructure/drift_document_workspace_repository.dart';
import '../../features/pedagogy/application/local_flashcard_scheduler.dart';
import '../../features/pedagogy/application/local_quiz_evaluator.dart';
import '../../features/pedagogy/application/pedagogy_repository.dart';
import '../../features/pedagogy/domain/pedagogy.dart';
import '../../features/pedagogy/infrastructure/drift_pedagogy_repository.dart';
import '../../features/sync/application/outbox_repository.dart';
import '../../features/sync/infrastructure/drift_outbox_repository.dart';
import '../../features/study_plan/application/load_today_plan.dart';
import '../../features/study_plan/application/adaptive_planning_repository.dart';
import '../../features/study_plan/application/generate_adaptive_today_plan.dart';
import '../../features/study_plan/domain/study_plan.dart';
import '../../features/study_plan/infrastructure/drift_study_plan_repository.dart';
import '../../features/study_plan/infrastructure/drift_adaptive_planning_repository.dart';
import '../database/app_database.dart';

final appDatabaseProvider = Provider<AppDatabase>((ref) {
  final database = AppDatabase();
  ref.onDispose(database.close);
  return database;
});

final academicProfileRepositoryProvider = Provider<AcademicProfileRepository>((ref) {
  return DriftAcademicProfileRepository(ref.watch(appDatabaseProvider),accountIdProvider:() async => (await ref.read(identityRepositoryProvider).currentSession())?.accountId);
});

final personalDocumentRepositoryProvider = Provider<PersonalDocumentRepository>((ref) {
  return DriftPersonalDocumentRepository(ref.watch(appDatabaseProvider));
});

final outboxRepositoryProvider = Provider<OutboxRepository>((ref) {
  return DriftOutboxRepository(ref.watch(appDatabaseProvider));
});

final localDocumentStoreProvider = Provider<LocalDocumentStore>((ref) {
  return createLocalDocumentStore();
});

final importPersonalDocumentProvider = Provider<ImportPersonalDocument>((ref) {
  return ImportPersonalDocument(
    repository: ref.watch(personalDocumentRepositoryProvider),
    store: ref.watch(localDocumentStoreProvider),
    outbox: ref.watch(outboxRepositoryProvider),
  );
});

final academicProfileProvider = StreamProvider((ref) {
  return ref.watch(academicProfileRepositoryProvider).watchActive();
});

final personalDocumentsProvider = StreamProvider<List<PersonalDocument>>((ref) {
  return ref.watch(personalDocumentRepositoryProvider).watchAll();
});

final documentWorkspaceRepositoryProvider = Provider<DocumentWorkspaceRepository>((ref) {
  return DriftDocumentWorkspaceRepository(ref.watch(appDatabaseProvider));
});

final personalDocumentByIdProvider = FutureProvider.family<PersonalDocument?, String>((ref, id) {
  return ref.watch(personalDocumentRepositoryProvider).getById(id);
});

final documentSectionsProvider = StreamProvider.family<List<DocumentSection>, String>((ref, id) {
  return ref.watch(documentWorkspaceRepositoryProvider).watchSections(id);
});

final documentAnnotationsProvider = StreamProvider.family<List<DocumentAnnotation>, String>((ref, id) {
  return ref.watch(documentWorkspaceRepositoryProvider).watchAnnotations(id);
});

final documentProgressProvider = StreamProvider.family<ReadingProgress?, String>((ref, id) {
  return ref.watch(documentWorkspaceRepositoryProvider).watchProgress(id);
});

final documentAnalysisProvider = StreamProvider.family<DocumentAnalysisSummary?, String>((ref, id) {
  return ref.watch(documentWorkspaceRepositoryProvider).watchAnalysis(id);
});

final pedagogyRepositoryProvider = Provider<PedagogyRepository>((ref) {
  return DriftPedagogyRepository(ref.watch(appDatabaseProvider));
});

final flashcardSchedulerProvider = Provider<LocalFlashcardScheduler>((ref) => LocalFlashcardScheduler());
final localQuizEvaluatorProvider = Provider<LocalQuizEvaluator>((ref) => const LocalQuizEvaluator());

final dueFlashcardsProvider = StreamProvider.family<List<StudyFlashcard>, String>((ref, courseId) {
  return ref.watch(pedagogyRepositoryProvider).watchDueFlashcards(courseId);
});

final courseSummariesProvider = StreamProvider.family<List<StudySummary>, String>((ref, courseId) {
  return ref.watch(pedagogyRepositoryProvider).watchSummaries(courseId);
});

final courseQuestionsProvider = StreamProvider.family<List<StudyQuizQuestion>, String>((ref, courseId) {
  return ref.watch(pedagogyRepositoryProvider).watchQuestions(courseId);
});

final courseErrorsProvider = StreamProvider.family<List<LearningError>, String>((ref, courseId) {
  return ref.watch(pedagogyRepositoryProvider).watchOpenErrors(courseId);
});


final studyPlanRepositoryProvider = Provider<StudyPlanRepository>((ref) => DriftStudyPlanRepository(ref.watch(appDatabaseProvider),accountIdProvider:() async => (await ref.read(identityRepositoryProvider).currentSession())?.accountId));
final generateTodayPlanProvider = Provider<GenerateTodayPlan>((ref) => GenerateTodayPlan(ref.watch(studyPlanRepositoryProvider)));
final todayPlanProvider = StreamProvider<List<StudyPlanItem>>((ref) => ref.watch(studyPlanRepositoryProvider).watchTodayPlan());
final upcomingEventsProvider = StreamProvider<List<AcademicEvent>>((ref) => ref.watch(studyPlanRepositoryProvider).watchUpcomingEvents());
final timetableProvider = StreamProvider<List<TimetableEntry>>((ref) => ref.watch(studyPlanRepositoryProvider).watchTimetable());

final adaptivePlanningRepositoryProvider = Provider<AdaptivePlanningRepository>((ref) => DriftAdaptivePlanningRepository(ref.watch(appDatabaseProvider),accountIdProvider:() async => (await ref.read(identityRepositoryProvider).currentSession())?.accountId));
final studyAvailabilityProvider = StreamProvider<List<AvailabilityRule>>((ref) => ref.watch(adaptivePlanningRepositoryProvider).watchAvailabilityRules());
final adaptiveTodayBlocksProvider = StreamProvider((ref) => ref.watch(adaptivePlanningRepositoryProvider).watchTodayBlocks());
final generateAdaptiveTodayPlanProvider = Provider((ref) => GenerateAdaptiveTodayPlan(studyRepository: ref.watch(studyPlanRepositoryProvider), adaptiveRepository: ref.watch(adaptivePlanningRepositoryProvider)));


final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
final sessionStoreProvider = Provider<SessionStore>((ref) => SecureSessionStore());
final identityRepositoryProvider = Provider<IdentityRepository>((ref) => ApiIdentityRepository(api: ref.watch(apiClientProvider), store: ref.watch(sessionStoreProvider), database: ref.watch(appDatabaseProvider)));
final authSessionProvider = FutureProvider<AuthSession?>((ref) => ref.watch(identityRepositoryProvider).currentSession());

final commerceRepositoryProvider = Provider<CommerceRepository>((ref) => DriftCommerceRepository(ref.watch(appDatabaseProvider)));
final commerceRemoteGatewayProvider = Provider<CommerceRemoteGateway>((ref) => ApiCommerceGateway(api: ref.watch(apiClientProvider), identity: ref.watch(identityRepositoryProvider)));
final combinedAccessProvider = FutureProvider<CombinedAccessView>((ref) async {
  return ref.watch(commerceRemoteGatewayProvider).getCombinedAccess();
});
/// Institution-scoped, authenticated snapshot. Never reuse a different tenant's rights.
final campusCombinedAccessProvider = FutureProvider.autoDispose.family<CombinedAccessView, String>((ref, institutionId) async {
  if (institutionId.trim().isEmpty) throw ArgumentError.value(institutionId, 'institutionId');
  return ref.watch(commerceRemoteGatewayProvider).getCombinedAccess(institutionId: institutionId);
});
final premiumPlansProvider = FutureProvider<List<PremiumPlan>>((ref) => ref.watch(commerceRemoteGatewayProvider).loadPlans());
final paymentProvidersProvider = FutureProvider<List<PaymentProviderOption>>((ref) => ref.watch(commerceRemoteGatewayProvider).loadProviders());
final entitlementProvider = StreamProvider<EntitlementSnapshot?>((ref) => ref.watch(commerceRepositoryProvider).watchEntitlement());
final paymentsProvider = StreamProvider<List<PaymentIntentView>>((ref) => ref.watch(commerceRepositoryProvider).watchPayments());
final receiptsProvider = StreamProvider<List<ReceiptView>>((ref) => ref.watch(commerceRepositoryProvider).watchReceipts());
final syncEntitlementProvider = Provider<SyncEntitlement>((ref) => SyncEntitlement(local: ref.watch(commerceRepositoryProvider), remote: ref.watch(commerceRemoteGatewayProvider)));

final assistantLocalRepositoryProvider = Provider<AssistantLocalRepository>((ref) => DriftAssistantRepository(ref.watch(appDatabaseProvider)));
final assistantRemoteGatewayProvider = Provider<AssistantRemoteGateway>((ref) => ApiAssistantGateway(api:ref.watch(apiClientProvider),identity:ref.watch(identityRepositoryProvider)));
final assistantConversationsProvider = StreamProvider<List<AssistantConversation>>((ref) => ref.watch(assistantLocalRepositoryProvider).watchConversations());
final assistantMessagesProvider = StreamProvider.family<List<AssistantMessage>, String>((ref, conversationId) => ref.watch(assistantLocalRepositoryProvider).watchMessages(conversationId));


final cloudSyncLocalRepositoryProvider = Provider<CloudSyncLocalRepository>((ref) => DriftCloudSyncRepository(ref.watch(appDatabaseProvider)));
final cloudSyncRemoteGatewayProvider = Provider<CloudSyncRemoteGateway>((ref) => ApiSyncGateway(api: ref.watch(apiClientProvider), identity: ref.watch(identityRepositoryProvider)));
final cloudSyncStateProvider = StreamProvider<CloudSyncState?>((ref) async* {
  final session=await ref.watch(identityRepositoryProvider).currentSession();
  if(session==null){yield null;return;}
  yield* ref.watch(cloudSyncLocalRepositoryProvider).watchState(session.accountId);
});
final syncConflictsProvider = StreamProvider<List<SyncConflictView>>((ref) async* {
  final session=await ref.watch(identityRepositoryProvider).currentSession();
  if(session==null){yield const [];return;}
  yield* ref.watch(cloudSyncLocalRepositoryProvider).watchOpenConflicts(session.accountId);
});
final syncDiagnosticsProvider = StreamProvider<SyncDiagnostics>((ref) async* {
  final session=await ref.watch(identityRepositoryProvider).currentSession();
  if(session==null){yield const SyncDiagnostics(pending:0,deadLetters:0,openConflicts:0,oldestPendingAt:null);return;}
  yield* ref.watch(cloudSyncLocalRepositoryProvider).watchDiagnostics(session.accountId);
});
final syncDevicesProvider = FutureProvider<List<SyncDeviceView>>((ref) async {
  final session=await ref.watch(identityRepositoryProvider).currentSession();
  if(session==null) return const [];
  return ref.watch(cloudSyncRemoteGatewayProvider).listDevices();
});
String _platformCode() {
  if (kIsWeb) return 'web';
  return switch (defaultTargetPlatform) {
    TargetPlatform.android => 'android',
    TargetPlatform.iOS => 'ios',
    TargetPlatform.windows => 'windows',
    TargetPlatform.macOS => 'macos',
    TargetPlatform.linux => 'linux',
    _ => 'unknown',
  };
}
final runCloudSyncProvider = Provider<RunCloudSync>((ref) => RunCloudSync(
  local: ref.watch(cloudSyncLocalRepositoryProvider),
  remote: ref.watch(cloudSyncRemoteGatewayProvider),
  platform: _platformCode(),
  deviceName: 'EduNova ${_platformCode()}',
  appVersion: '0.11.0',
  accountIdProvider: () async => (await ref.read(identityRepositoryProvider).currentSession())?.accountId,
));

final libraryLocalRepositoryProvider = Provider<LibraryLocalRepository>((ref) => DriftLibraryRepository(
  ref.watch(appDatabaseProvider),
  accountIdProvider: () async => (await ref.read(identityRepositoryProvider).currentSession())?.accountId,
));
final libraryRemoteGatewayProvider = Provider<LibraryRemoteGateway>((ref) => ApiLibraryGateway(api: ref.watch(apiClientProvider), identity: ref.watch(identityRepositoryProvider)));
final libraryCoursesProvider = StreamProvider<List<LibraryCourseView>>((ref) => ref.watch(libraryLocalRepositoryProvider).watchCourses());
final refreshLibraryCatalogProvider = Provider<RefreshLibraryCatalog>((ref) => RefreshLibraryCatalog(ref.watch(libraryLocalRepositoryProvider), ref.watch(libraryRemoteGatewayProvider)));
final libraryResourcesProvider = StreamProvider.family<List<LibraryResourceView>, String>((ref, versionId) => ref.watch(libraryLocalRepositoryProvider).watchResources(versionId));


final deliveryRemoteGatewayProvider = Provider<DeliveryRemoteGateway>((ref) => ApiDeliveryGateway(
  api: ref.watch(apiClientProvider), identity: ref.watch(identityRepositoryProvider),
));
final offlineDeliveryRepositoryProvider = Provider<OfflineDeliveryRepository>((ref) => DriftOfflineDeliveryRepository(ref.watch(appDatabaseProvider)));
final offlineResourceStoreProvider = Provider<OfflineResourceStore>((ref) => createOfflineResourceStore(ref.watch(appDatabaseProvider)));
final downloadResourceProvider = Provider<DownloadResource>((ref) => DownloadResource(
  remote: ref.watch(deliveryRemoteGatewayProvider), local: ref.watch(offlineDeliveryRepositoryProvider),
  store: ref.watch(offlineResourceStoreProvider), identity: ref.watch(identityRepositoryProvider),
));
final offlineResourceStateProvider = StreamProvider.family<OfflineResourceState?, String>((ref,id)=>ref.watch(offlineDeliveryRepositoryProvider).watchState(id));
final contentCachePolicyProvider = FutureProvider<ContentCachePolicy>((ref)=>ref.watch(offlineDeliveryRepositoryProvider).loadPolicy());

final offlineResourcesProvider = StreamProvider<List<OfflineResourceState>>((ref)=>ref.watch(offlineDeliveryRepositoryProvider).watchAll());
final runCacheCleanupProvider = Provider<RunCacheCleanup>((ref)=>RunCacheCleanup(local:ref.watch(offlineDeliveryRepositoryProvider),store:ref.watch(offlineResourceStoreProvider)));
final runDownloadQueueProvider = Provider<RunDownloadQueue>((ref)=>RunDownloadQueue(local:ref.watch(offlineDeliveryRepositoryProvider),remoteLibrary:ref.watch(libraryRemoteGatewayProvider),downloader:ref.watch(downloadResourceProvider)));

final queueCourseOfflineProvider = Provider<QueueCourseOffline>((ref)=>QueueCourseOffline(local:ref.watch(offlineDeliveryRepositoryProvider),remoteLibrary:ref.watch(libraryRemoteGatewayProvider),queue:ref.watch(runDownloadQueueProvider)));


final engagementRepositoryProvider = Provider<EngagementRepository>((ref)=>DriftEngagementRepository(ref.watch(appDatabaseProvider)));
final engagementRemoteGatewayProvider = Provider<ApiEngagementGateway>((ref)=>ApiEngagementGateway(api:ref.watch(apiClientProvider),identity:ref.watch(identityRepositoryProvider)));
final remotePushRegistrarProvider = Provider<RemotePushRegistrar>((ref){ final r=RemotePushRegistrar(ref.watch(engagementRemoteGatewayProvider)); ref.onDispose(r.dispose); return r; });
final engagementPreferencesProvider = StreamProvider<EngagementPreferences>((ref)=>ref.watch(engagementRepositoryProvider).watchPreferences());
final engagementDaysProvider = StreamProvider<List<EngagementDailyStat>>((ref)=>ref.watch(engagementRepositoryProvider).watchRecentDays(limit:14));
final upcomingLocalNotificationsProvider = StreamProvider<List<LocalNotificationView>>((ref)=>ref.watch(engagementRepositoryProvider).watchUpcomingNotifications(limit:20));
final recentNotificationHistoryProvider = StreamProvider<List<LocalNotificationView>>((ref)=>ref.watch(engagementRepositoryProvider).watchNotificationHistory(limit:20));
final localNotificationSchedulerProvider = Provider((ref)=>createLocalNotificationScheduler());
final rescheduleLocalNotificationsProvider = Provider((ref)=>RescheduleLocalNotifications(ref.watch(engagementRepositoryProvider),ref.watch(localNotificationSchedulerProvider)));
final localStreakProvider = FutureProvider<StreakView>((ref)=>ref.watch(engagementRepositoryProvider).computeLocalStreak(DateTime.now()));
final audioRepositoryProvider = Provider<AudioRepository>((ref)=>DriftAudioRepository(ref.watch(appDatabaseProvider)));
final ttsNarratorProvider = Provider<TtsNarrator>((ref){final narrator=DeviceTtsNarrator(); ref.onDispose(narrator.stop); return narrator;});

final audioPlaybackProvider = StreamProvider.family<AudioPlaybackState?, String>((ref,id)=>ref.watch(audioRepositoryProvider).watchPlayback(id));
final audioBookmarksProvider = StreamProvider.family<List<AudioBookmark>, String>((ref,id)=>ref.watch(audioRepositoryProvider).watchBookmarks(id));

final analyticsRepositoryProvider = Provider<AnalyticsRepository>((ref)=>DriftAnalyticsRepository(ref.watch(appDatabaseProvider)));
final analyticsEngineProvider = Provider<LocalAnalyticsEngine>((ref)=>const LocalAnalyticsEngine());
final analyticsSnapshotProvider = FutureProvider<AnalyticsSnapshot>((ref)=>ref.watch(analyticsRepositoryProvider).buildSnapshot(DateTime.now()));
final analyticsReportProvider = FutureProvider<AnalyticsReport>((ref) async {
  final snapshot=await ref.watch(analyticsSnapshotProvider.future);
  return ref.watch(analyticsEngineProvider).build(snapshot);
});
final analyticsFeedbackProvider = StreamProvider<List<RecommendationFeedback>>((ref)=>ref.watch(analyticsRepositoryProvider).watchFeedback());


// Phase 14/15 — restricted Campus intelligence: remote-only; no offline copies.
final campusIntelligenceGatewayProvider = Provider<CampusIntelligenceGateway>((ref) =>
  CampusIntelligenceGateway(api: ref.watch(apiClientProvider), identity: ref.watch(identityRepositoryProvider)));

// Phase 16 physical resources: tenant-bound API, no local caching.
final campusServicesGatewayProvider = Provider<CampusServicesGateway>((ref) =>
  CampusServicesGateway(api: ref.watch(apiClientProvider), identity: ref.watch(identityRepositoryProvider)));

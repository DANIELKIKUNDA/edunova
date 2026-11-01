import '../features/commerce/presentation/platform_campus_offers_page.dart';
import '../features/campus_services/presentation/campus_alumni_page.dart';
import '../features/campus_services/presentation/campus_academic_resources_page.dart';
import '../features/campus_services/presentation/campus_services_page.dart';
import '../features/campus_services/presentation/campus_events_page.dart';
import '../features/campus_services/presentation/physical_library_page.dart';
import 'package:go_router/go_router.dart';
import '../features/identity/infrastructure/secure_session_store.dart';

import '../features/calendar/presentation/calendar_page.dart';
import '../features/calendar/presentation/schedule_import_page.dart';
import '../features/courses/presentation/courses_page.dart';
import '../features/document_engine/presentation/document_workspace_page.dart';
import '../features/home/presentation/home_page.dart';
import '../features/onboarding/presentation/bootstrap_page.dart';
import '../features/onboarding/presentation/onboarding_page.dart';
import '../features/profile/presentation/profile_page.dart';
import '../features/identity/presentation/login_page.dart';
import '../features/identity/presentation/register_page.dart';
import '../features/identity/presentation/security_page.dart';
import '../features/identity/presentation/recovery_page.dart';
import '../features/commerce/presentation/premium_page.dart';
import '../features/assistant/presentation/assistant_page.dart';
import '../features/assistant/presentation/assistant_history_page.dart';
import '../features/pedagogy/presentation/pedagogy_hub_page.dart';
import '../features/pedagogy/presentation/flashcard_session_page.dart';
import '../features/pedagogy/presentation/quiz_session_page.dart';
import '../features/revision/presentation/revision_page.dart';
import '../features/revision/presentation/planning_preferences_page.dart';
import '../features/sync/presentation/sync_status_page.dart';
import '../features/library/presentation/library_course_page.dart';
import '../features/delivery/presentation/offline_storage_page.dart';
import '../features/engagement/presentation/engagement_page.dart';
import '../features/audio/presentation/audio_summary_page.dart';
import '../features/analytics/presentation/analytics_page.dart';
import '../shared/presentation/edunova_shell.dart';
import '../features/study_workspace/presentation/study_workspace_page.dart';
import '../features/adaptive_learning/presentation/adaptive_learning_page.dart';
import '../features/study_planner/presentation/adaptive_study_planner_page.dart';
import '../features/remediation/presentation/remediation_page.dart';
import '../features/campus/presentation/campus_page.dart';
import '../features/campus_intelligence/presentation/institution_intelligence_page.dart';
import '../features/pilot/presentation/pilot_center_page.dart';

// Set only after BootstrapPage has checked local SQLite and downloaded files.
bool _anonymousBootstrapVerified = false;
void markCleanAnonymousBootstrapVerified() => _anonymousBootstrapVerified = true;

final edunovaRouter = GoRouter(
  initialLocation: '/bootstrap',
  // Fail closed for direct navigation and deep links: no private screen may be
  // constructed before the durable installation identity has been checked.
  // Bootstrap remains responsible for ownerless legacy SQLite/file inspection.
  redirect: (context, state) async {
    final path = state.uri.path;
    const publicPaths = {'/bootstrap', '/login', '/register', '/recovery'};
    if (publicPaths.contains(path)) return null;
    try {
      final store = SecureSessionStore();
      final session = await store.read();
      if (session != null) return null;
      final owner = await store.ownerAccountId();
      if (owner == null && _anonymousBootstrapVerified) return null;
      // An empty installation may use the local-first experience, but must
      // pass bootstrap's legacy-data and offline-file checks first.
      return '/bootstrap';
    } catch (_) {
      // Secure storage failure or inconsistent ownership must never allow a
      // private route to render.
      return '/login';
    }
  },
  routes: [
    GoRoute(path: '/bootstrap', builder: (_, __) => const BootstrapPage()),
    GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingPage()),
    GoRoute(path: '/login', builder: (_, __) => const LoginPage()),
    GoRoute(path: '/register', builder: (_, __) => const RegisterPage()),
    GoRoute(path: '/security', builder: (_, __) => const SecurityPage()),
    GoRoute(path: '/recovery', builder: (_, __) => const RecoveryPage()),
    GoRoute(path: '/platform/campus-offers', builder: (_, __) => const PlatformCampusOffersPage()),
    GoRoute(path: '/premium', builder: (_, __) => const PremiumPage()),
    GoRoute(path: '/sync', builder: (_, __) => const SyncStatusPage()),
    GoRoute(path: '/offline-storage', builder: (_, __) => const OfflineStoragePage()),
    GoRoute(path: '/engagement', builder: (_, __) => const EngagementPage()),
    GoRoute(path: '/analytics', builder: (_, __) => const AnalyticsPage()),
    GoRoute(path: '/adaptive-learning', builder: (_, __) => const AdaptiveLearningPage()),
    GoRoute(path: '/study-planner', builder: (_, __) => const AdaptiveStudyPlannerPage()),
    GoRoute(path: '/remediation', builder: (_, __) => const RemediationPage()),
    GoRoute(path: '/campus', builder: (_, __) => const CampusPage()),
    GoRoute(path: '/campus/alumni/:institutionId', builder: (_, state) =>
      CampusAlumniPage(institutionId: state.pathParameters['institutionId']!)),
    GoRoute(path: '/campus/academic-rooms/:institutionId', builder: (_, state) =>
      CampusAcademicResourcesPage(institutionId: state.pathParameters['institutionId']!)),
    GoRoute(path: '/campus/services/:institutionId', builder: (_, state) =>
      CampusServicesPage(institutionId: state.pathParameters['institutionId']!)),
    GoRoute(path: '/campus/events/:institutionId', builder: (_, state) =>
      CampusEventsPage(institutionId: state.pathParameters['institutionId']!)),
    GoRoute(path: '/campus/physical-library/:institutionId', builder: (_, state) =>
      PhysicalLibraryPage(institutionId: state.pathParameters['institutionId']!)),
    GoRoute(path: '/campus/intelligence/:institutionId', builder: (_, state) =>
      InstitutionIntelligencePage(institutionId: state.pathParameters['institutionId']!)),
    GoRoute(path: '/pilot', builder: (_, __) => const PilotCenterPage()),
    GoRoute(path: '/audio/:courseId', builder: (_, state) => AudioSummaryPage(courseId: state.pathParameters['courseId']!)),
    GoRoute(path: '/library/:courseId', builder: (_, state) => LibraryCoursePage(courseId: state.pathParameters['courseId']!, title: state.uri.queryParameters['title'] ?? 'Cours EduNova')),
    GoRoute(path: '/assistant', builder: (_, state) => AssistantPage(courseId: state.uri.queryParameters['courseId'], documentId: state.uri.queryParameters['documentId'], subjectDomain: state.uri.queryParameters['subjectDomain'] ?? 'general', existingConversationId: state.uri.queryParameters['conversationId'])),
    GoRoute(path: '/assistant/history', builder: (_, __) => const AssistantHistoryPage()),
    GoRoute(path: '/calendar/import', builder: (_, __) => const ScheduleImportPage()),
    GoRoute(path: '/revision/planning-settings', builder: (_, __) => const PlanningPreferencesPage()),
    GoRoute(
      path: '/documents/:id',
      builder: (_, state) => DocumentWorkspacePage(documentId: state.pathParameters['id']!, initialPage: int.tryParse(state.uri.queryParameters['page'] ?? '')),
    ),
    GoRoute(path: '/workspace/:courseId', builder: (_, state) => StudyWorkspacePage(courseId: state.pathParameters['courseId']!, title: state.uri.queryParameters['title'] ?? 'Cours EduNova')),
    GoRoute(
      path: '/study/:courseId',
      builder: (_, state) => PedagogyHubPage(
        courseId: state.pathParameters['courseId']!,
        title: state.uri.queryParameters['title'] ?? 'Cours',
      ),
    ),
    GoRoute(
      path: '/study/:courseId/flashcards',
      builder: (_, state) => FlashcardSessionPage(
        courseId: state.pathParameters['courseId']!,
        title: state.uri.queryParameters['title'] ?? 'Flashcards',
      ),
    ),
    GoRoute(
      path: '/study/:courseId/quiz',
      builder: (_, state) => QuizSessionPage(
        courseId: state.pathParameters['courseId']!,
        title: state.uri.queryParameters['title'] ?? 'Quiz',
      ),
    ),
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) => EduNovaShell(navigationShell: navigationShell),
      branches: [
        StatefulShellBranch(routes: [
          GoRoute(path: '/home', builder: (_, __) => const HomePage()),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(path: '/courses', builder: (_, __) => const CoursesPage()),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(path: '/revision', builder: (_, __) => const RevisionPage()),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(path: '/calendar', builder: (_, __) => const CalendarPage()),
        ]),
        StatefulShellBranch(routes: [
          GoRoute(path: '/profile', builder: (_, __) => const ProfilePage()),
        ]),
      ],
    ),
  ],
);

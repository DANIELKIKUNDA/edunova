import 'package:edunova/src/core/theme/edunova_theme.dart';
import 'package:edunova/src/features/home/presentation/home_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:edunova/src/core/di/providers.dart';

void main() {
  testWidgets('home renders preparation for an empty local account', (tester) async {
    await tester.pumpWidget(ProviderScope(overrides: [
      todayPlanProvider.overrideWith((ref) => Stream.value([])),
      upcomingEventsProvider.overrideWith((ref) => Stream.value([])),
      libraryCoursesProvider.overrideWith((ref) => Stream.value([])),
      engagementPreferencesProvider.overrideWith((ref) => const Stream.empty()),
      engagementDaysProvider.overrideWith((ref) => Stream.value([])),
      upcomingLocalNotificationsProvider.overrideWith((ref) => Stream.value([])),
      localStreakProvider.overrideWith((ref) async => throw StateError('No local streak yet')),
      analyticsReportProvider.overrideWith((ref) async => throw StateError('No local analytics yet')),
    ], child: MaterialApp(theme: EduNovaTheme.light, home: const Scaffold(body: HomePage()))));
    await tester.pump();
    expect(find.text('Prêt à avancer ?'), findsOneWidget);
    expect(find.text('Ton plan est prêt à être construit'), findsOneWidget);
    expect(find.text('Ouvrir Réviser'), findsOneWidget);
  });
}

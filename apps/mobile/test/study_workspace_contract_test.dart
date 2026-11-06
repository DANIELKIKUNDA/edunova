import 'package:edunova/src/features/study_workspace/presentation/study_workspace_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('compact workspace keeps navigation and restores it after focus', (tester) async {
    tester.view.resetPhysicalSize();
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(700, 1000);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const MaterialApp(home: StudyWorkspacePage(courseId: 'test-course', title: 'Test course')));
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.byTooltip('Disponible hors connexion'), findsOneWidget);
    await tester.tap(find.byTooltip('Mode Focus'));
    await tester.pumpAndSettle();
    expect(find.byType(NavigationBar), findsNothing);
    expect(find.byTooltip('Disponible hors connexion'), findsNothing);
    expect(find.text('Concepts fondamentaux'), findsOneWidget);
    await tester.tap(find.byTooltip('Quitter le mode Focus'));
    await tester.pumpAndSettle();
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('desktop workspace keeps content while focus hides side panels', (tester) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(1500, 1100);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const MaterialApp(home: StudyWorkspacePage(courseId: 'test-course', title: 'Test course')));
    expect(find.byType(NavigationBar), findsNothing);
    expect(find.text('Plan du cours'), findsOneWidget);
    expect(find.text('Ton coach'), findsOneWidget);
    expect(find.text('Exam Mode'), findsOneWidget);
    expect(find.widgetWithText(TextButton, 'Configurer'), findsOneWidget);
    await tester.tap(find.byTooltip('Mode Focus'));
    await tester.pumpAndSettle();
    expect(find.text('Plan du cours'), findsNothing);
    expect(find.text('Ton coach'), findsNothing);
    expect(find.text('Concepts fondamentaux'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

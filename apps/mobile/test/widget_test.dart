import 'package:edunova/src/core/theme/edunova_theme.dart';
import 'package:edunova/src/features/home/presentation/home_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('home renders premium preparation card', (tester) async {
    await tester.pumpWidget(MaterialApp(theme: EduNovaTheme.light, home: const HomePage()));
    expect(find.text('Biochimie'), findsWidgets);
    expect(find.text('Continuer ma préparation'), findsOneWidget);
  });
}

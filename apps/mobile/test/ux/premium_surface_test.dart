import 'package:edunova/src/core/theme/edunova_theme.dart';
import 'package:edunova/src/shared/presentation/widgets/premium_surface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('PremiumPanel remains usable with large text', (tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: EduNovaTheme.light,
      home: MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.linear(2.0)),
        child: const Scaffold(
          body: SizedBox(
            width: 360,
            child: PremiumPanel(
              child: Row(children: [
                Icon(Icons.school_rounded),
                SizedBox(width: 12),
                Expanded(child: Text('Une interface premium doit rester lisible lorsque le texte est agrandi.')),
              ]),
            ),
          ),
        ),
      ),
    ));
    expect(find.textContaining('interface premium'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('EmptyStateCard exposes clear title and action', (tester) async {
    await tester.pumpWidget(MaterialApp(
      theme: EduNovaTheme.light,
      home: Scaffold(
        body: EmptyStateCard(
          icon: Icons.notifications_none_rounded,
          title: 'Aucun rappel',
          message: 'Tout est calme.',
          action: FilledButton(onPressed: () {}, child: const Text('Configurer')),
        ),
      ),
    ));
    expect(find.text('Aucun rappel'), findsOneWidget);
    expect(find.text('Configurer'), findsOneWidget);
  });
}

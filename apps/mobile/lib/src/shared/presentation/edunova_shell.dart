import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/tokens.dart';

class EduNovaShell extends StatelessWidget {
  const EduNovaShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  static const _items = [
    (Icons.home_outlined, Icons.home_rounded, 'Accueil'),
    (Icons.auto_stories_outlined, Icons.auto_stories_rounded, 'Mes cours'),
    (Icons.bolt_outlined, Icons.bolt_rounded, 'Réviser'),
    (Icons.calendar_month_outlined, Icons.calendar_month_rounded, 'Calendrier'),
    (Icons.person_outline_rounded, Icons.person_rounded, 'Moi'),
  ];

  void _select(int index) => navigationShell.goBranch(
        index,
        initialLocation: index == navigationShell.currentIndex,
      );

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final wide = constraints.maxWidth >= EduNovaLayout.railBreakpoint;
      if (!wide) {
        return Scaffold(
          body: SafeArea(child: navigationShell),
          bottomNavigationBar: DecoratedBox(
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: Theme.of(context).colorScheme.outlineVariant.withValues(alpha: .45))),
            ),
            child: NavigationBar(
              selectedIndex: navigationShell.currentIndex,
              onDestinationSelected: _select,
              destinations: _items
                  .map((item) => NavigationDestination(
                        icon: Icon(item.$1),
                        selectedIcon: Icon(item.$2),
                        label: item.$3,
                      ))
                  .toList(),
            ),
          ),
        );
      }

      final extended = constraints.maxWidth >= EduNovaLayout.extendedRailBreakpoint;
      final scheme = Theme.of(context).colorScheme;
      return Scaffold(
        body: Row(children: [
          SafeArea(
            right: false,
            child: NavigationRail(
              extended: extended,
              minExtendedWidth: 220,
              selectedIndex: navigationShell.currentIndex,
              onDestinationSelected: _select,
              labelType: extended ? NavigationRailLabelType.none : NavigationRailLabelType.all,
              leading: Padding(
                padding: const EdgeInsets.fromLTRB(10, 16, 10, 24),
                child: Semantics(
                  label: 'EduNova',
                  child: Container(
                    width: extended ? 176 : 48,
                    height: 48,
                    padding: EdgeInsets.symmetric(horizontal: extended ? 12 : 0),
                    decoration: BoxDecoration(
                      color: scheme.primaryContainer.withValues(alpha: .55),
                      borderRadius: BorderRadius.circular(EduNovaRadius.md),
                    ),
                    child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Icon(Icons.school_rounded, color: scheme.primary),
                      if (extended) ...[
                        const SizedBox(width: 10),
                        Expanded(child: Text('EduNova', style: TextStyle(color: scheme.primary, fontWeight: FontWeight.w900, fontSize: 18))),
                      ],
                    ]),
                  ),
                ),
              ),
              destinations: _items
                  .map((item) => NavigationRailDestination(
                        icon: Icon(item.$1),
                        selectedIcon: Icon(item.$2),
                        label: Text(item.$3),
                      ))
                  .toList(),
            ),
          ),
          VerticalDivider(width: 1, color: scheme.outlineVariant.withValues(alpha: .45)),
          Expanded(child: SafeArea(left: false, child: navigationShell)),
        ]),
      );
    });
  }
}

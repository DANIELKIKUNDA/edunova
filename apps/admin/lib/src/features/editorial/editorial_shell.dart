import 'package:flutter/material.dart';

import 'content_list_page.dart';
import 'content_factory_page.dart';
import 'dashboard_page.dart';
import 'editorial_api.dart';
import 'ingestion_page.dart';
import 'publication_center_page.dart';
import 'question_factory_page.dart';
import 'team_page.dart';

class EditorialShell extends StatefulWidget {
  final EditorialApi api;
  final Future<void> Function() onLogout;
  const EditorialShell({super.key, required this.api, required this.onLogout});
  @override State<EditorialShell> createState() => _EditorialShellState();
}

class _EditorialShellState extends State<EditorialShell> {
  int index = 0;
  String? presetState;
  static const labels = ['Vue d’ensemble','Ingestion','Content Factory','Contenus','À relire','Prêts à publier','Publication Center','Question Factory','Équipe'];

  void openSection(int i) {
    setState(() {
      index = i;
      presetState = i == 4 ? 'in_review' : i == 5 ? 'approved' : null;
    });
  }

  Widget _page() => switch(index) {
    0 => EditorialDashboardPage(api: widget.api, onOpenSection: (legacy) {
      // Dashboard v0.12.1 used indexes before LOT 12 insertion.
      final mapped = switch(legacy) { 0 => 0, 1 => 3, 2 => 4, 3 => 5, _ => 6 };
      openSection(mapped);
    }),
    1 => IngestionPage(api: widget.api),
    2 => ContentFactoryPage(api: widget.api),
    3 => ContentListPage(api: widget.api, presetState: presetState),
    4 => ContentListPage(api: widget.api, presetState: 'in_review'),
    5 => ContentListPage(api: widget.api, presetState: 'approved'),
    6 => PublicationCenterPage(api: widget.api),
    7 => QuestionFactoryPage(api: widget.api),
    _ => TeamPage(api: widget.api),
  };

  Future<void> _openMore() async {
    final selected = await showModalBottomSheet<int>(context: context, builder: (c) => SafeArea(child: Column(mainAxisSize: MainAxisSize.min, children: [
      ListTile(leading: const Icon(Icons.fact_check_outlined), title: const Text('À relire'), onTap: () => Navigator.pop(c, 4)),
      ListTile(leading: const Icon(Icons.publish_outlined), title: const Text('Prêts à publier'), onTap: () => Navigator.pop(c, 5)),
      ListTile(leading: const Icon(Icons.group_outlined), title: const Text('Équipe'), onTap: () => Navigator.pop(c, 8)),
    ])));
    if (selected != null) openSection(selected);
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final wide = width >= 920;
    final veryWide = width >= 1280;
    final selectedMobile = index <= 2 ? index : 3;
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          Container(width: 34, height: 34, decoration: BoxDecoration(color: Theme.of(context).colorScheme.primary, borderRadius: BorderRadius.circular(11)), child: Icon(Icons.auto_awesome_rounded, color: Theme.of(context).colorScheme.onPrimary, size: 20)),
          const SizedBox(width: 10),
          Text(index == 0 ? 'EduNova Studio' : labels[index], style: const TextStyle(fontWeight: FontWeight.w800)),
        ]),
        actions: [
          if (veryWide) const Padding(padding: EdgeInsets.only(right: 8), child: Center(child: Text('Back-office privé'))),
          IconButton(tooltip: 'Déconnexion', onPressed: () async => widget.onLogout(), icon: const Icon(Icons.logout_rounded)),
        ],
      ),
      body: Row(children: [
        if (wide) NavigationRail(
          extended: veryWide,
          minExtendedWidth: 230,
          selectedIndex: index,
          onDestinationSelected: openSection,
          labelType: veryWide ? NavigationRailLabelType.none : NavigationRailLabelType.all,
          destinations: const [
            NavigationRailDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard_rounded), label: Text('Vue d’ensemble')),
            NavigationRailDestination(icon: Icon(Icons.factory_outlined), selectedIcon: Icon(Icons.factory_rounded), label: Text('Ingestion')),
            NavigationRailDestination(icon: Icon(Icons.precision_manufacturing_outlined), selectedIcon: Icon(Icons.precision_manufacturing_rounded), label: Text('Content Factory')),
            NavigationRailDestination(icon: Icon(Icons.library_books_outlined), selectedIcon: Icon(Icons.library_books_rounded), label: Text('Contenus')),
            NavigationRailDestination(icon: Icon(Icons.fact_check_outlined), selectedIcon: Icon(Icons.fact_check_rounded), label: Text('À relire')),
            NavigationRailDestination(icon: Icon(Icons.publish_outlined), selectedIcon: Icon(Icons.publish_rounded), label: Text('Publication')),
            NavigationRailDestination(icon: Icon(Icons.rocket_launch_outlined), selectedIcon: Icon(Icons.rocket_launch_rounded), label: Text('Publication Center')),
            NavigationRailDestination(icon: Icon(Icons.psychology_alt_outlined), selectedIcon: Icon(Icons.psychology_alt_rounded), label: Text('Question Factory')),
            NavigationRailDestination(icon: Icon(Icons.group_outlined), selectedIcon: Icon(Icons.group_rounded), label: Text('Équipe')),
          ],
        ),
        if (wide) const VerticalDivider(width: 1),
        Expanded(child: _page()),
      ]),
      bottomNavigationBar: wide ? null : NavigationBar(
        selectedIndex: selectedMobile,
        onDestinationSelected: (i) { if (i == 3) { _openMore(); } else { openSection(i); } },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard_rounded), label: 'Accueil'),
          NavigationDestination(icon: Icon(Icons.factory_outlined), selectedIcon: Icon(Icons.factory_rounded), label: 'Ingestion'),
          NavigationDestination(icon: Icon(Icons.precision_manufacturing_outlined), selectedIcon: Icon(Icons.precision_manufacturing_rounded), label: 'Factory'),
          NavigationDestination(icon: Icon(Icons.more_horiz_rounded), label: 'Plus'),
        ],
      ),
    );
  }
}

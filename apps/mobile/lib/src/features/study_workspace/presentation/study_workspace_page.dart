import 'package:flutter/material.dart';

class StudyWorkspacePage extends StatefulWidget {
  const StudyWorkspacePage({super.key, required this.courseId, required this.title});
  final String courseId;
  final String title;
  @override State<StudyWorkspacePage> createState() => _StudyWorkspacePageState();
}

class _StudyWorkspacePageState extends State<StudyWorkspacePage> {
  int tab = 0;
  bool focus = false;
  double progress = .42;
  int cardSide = 0;
  int quizChoice = -1;
  final modes = const [
    ('Lire', Icons.menu_book_rounded), ('Réviser', Icons.bolt_rounded),
    ('Cartes', Icons.style_rounded), ('Quiz', Icons.quiz_rounded),
    ('Exercices', Icons.calculate_rounded),
  ];

  @override Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final wide = width >= 980;
    return Scaffold(
      appBar: AppBar(
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(widget.title, maxLines: 1, overflow: TextOverflow.ellipsis),
          Text('Espace d’étude · ${(progress * 100).round()}% du chapitre', style: Theme.of(context).textTheme.labelSmall),
        ]),
        actions: [
          if (!focus) _SessionPill(minutes: 24),
          IconButton(tooltip: focus ? 'Quitter le mode Focus' : 'Mode Focus', onPressed: () => setState(() => focus = !focus), icon: Icon(focus ? Icons.fullscreen_exit_rounded : Icons.center_focus_strong_rounded)),
          if (!focus) IconButton(tooltip: 'Disponible hors connexion', onPressed: () {}, icon: const Icon(Icons.offline_pin_rounded)),
        ],
      ),
      body: SafeArea(child: AnimatedSwitcher(duration: const Duration(milliseconds: 240), child: wide ? _desktop(context) : _mobile(context))),
      bottomNavigationBar: wide || focus ? null : NavigationBar(selectedIndex: tab, onDestinationSelected: (v) => setState(() => tab = v), destinations: [for (final m in modes) NavigationDestination(icon: Icon(m.$2), selectedIcon: Icon(m.$2), label: m.$1)]),
    );
  }

  Widget _desktop(BuildContext c) => Row(children: [
    if (!focus) SizedBox(width: 270, child: _outline(c)),
    Expanded(child: _content(c)),
    if (!focus) SizedBox(width: 326, child: _coach(c)),
  ]);
  Widget _mobile(BuildContext c) => switch (tab) {0 => _content(c), 1 => _quickReview(c), 2 => _flashcards(c), 3 => _quiz(c), _ => _exercises(c)};

  Widget _outline(BuildContext c) => Container(
    margin: const EdgeInsets.all(12), padding: const EdgeInsets.all(12),
    decoration: _softBox(c),
    child: ListView(children: [
      Row(children: [Icon(Icons.format_list_bulleted_rounded, color: Theme.of(c).colorScheme.primary), const SizedBox(width: 8), Text('Plan du cours', style: Theme.of(c).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900))]),
      const SizedBox(height: 14),
      for (final x in const [('1. Introduction', true), ('2. Concepts fondamentaux', false), ('3. Applications', false), ('4. Synthèse', false)])
        ListTile(dense: true, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)), leading: Icon(x.$1.startsWith('2') ? Icons.play_circle_fill_rounded : x.$2 ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded), title: Text(x.$1), selected: x.$1.startsWith('2'), selectedTileColor: Theme.of(c).colorScheme.primaryContainer.withValues(alpha: .45)),
    ]),
  );

  Widget _content(BuildContext c) {
    final scheme = Theme.of(c).colorScheme;
    return ListView(padding: EdgeInsets.fromLTRB(focus ? 28 : 20, 20, focus ? 28 : 20, 100), children: [
      Semantics(header: true, child: Text('Concepts fondamentaux', style: Theme.of(c).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w900))),
      const SizedBox(height: 5),
      Text('Reprise exacte · dernière position mémorisée', style: TextStyle(color: scheme.onSurfaceVariant)),
      const SizedBox(height: 18),
      Row(children: [Expanded(child: ClipRRect(borderRadius: BorderRadius.circular(20), child: LinearProgressIndicator(value: progress, minHeight: 8))), const SizedBox(width: 12), Text('${(progress * 100).round()}%', style: const TextStyle(fontWeight: FontWeight.w900))]),
      const SizedBox(height: 28),
      Text('Comprendre avant de mémoriser', style: Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
      const SizedBox(height: 10),
      Text('Votre contenu EduNova apparaît ici avec une typographie confortable, une navigation par chapitre et une reprise précise. Les outils de révision restent liés au contexte étudié.', style: Theme.of(c).textTheme.bodyLarge?.copyWith(height: 1.65)),
      const SizedBox(height: 24),
      if (!focus) _ToolDeck(onMode: (i) => setState(() => tab = i)),
      const SizedBox(height: 22),
      _MasteryJourney(progress: .6),
      if (focus) ...[const SizedBox(height: 24), Center(child: FilledButton.icon(onPressed: () => setState(() => focus = false), icon: const Icon(Icons.check_rounded), label: const Text('Terminer le Focus')))],
    ]);
  }

  Widget _coach(BuildContext c) => Container(
    margin: const EdgeInsets.fromLTRB(0, 12, 12, 12), padding: const EdgeInsets.all(18), decoration: _softBox(c),
    child: ListView(children: [
      Text('Ton coach', style: Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
      const SizedBox(height: 4), Text('Priorités calculées pour aujourd’hui', style: TextStyle(color: Theme.of(c).colorScheme.onSurfaceVariant)),
      const SizedBox(height: 14),
      const _Metric(icon: Icons.style_rounded, value: '18', label: 'cartes dues'),
      const _Metric(icon: Icons.rule_rounded, value: '4', label: 'erreurs à revoir'),
      const _Metric(icon: Icons.local_fire_department_rounded, value: '35 min', label: 'objectif restant'),
      const Divider(height: 28),
      _ExamCard(onTap: () {}),
      const SizedBox(height: 14),
      FilledButton.icon(onPressed: () {}, icon: const Icon(Icons.play_arrow_rounded), label: const Text('Continuer le parcours')),
    ]),
  );

  Widget _quickReview(BuildContext c) => _modeShell(c, 'Révision rapide', '5 minutes pour consolider l’essentiel', Icons.bolt_rounded, [
    _DelightCard(icon: Icons.lightbulb_rounded, title: 'Idée clé', text: 'Revois les notions à forte valeur avant de passer aux questions.'),
    _DelightCard(icon: Icons.rule_rounded, title: '4 erreurs à reprendre', text: 'EduNova privilégie ce que tu n’as pas encore consolidé.'),
  ]);

  Widget _flashcards(BuildContext c) => _modeShell(c, 'Flashcards', '18 cartes dues · répétition espacée', Icons.style_rounded, [
    GestureDetector(onTap: () => setState(() => cardSide = 1 - cardSide), child: AnimatedSwitcher(duration: const Duration(milliseconds: 220), child: Container(key: ValueKey(cardSide), constraints: const BoxConstraints(minHeight: 230), padding: const EdgeInsets.all(28), decoration: _softBox(c), child: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [Icon(cardSide == 0 ? Icons.psychology_alt_rounded : Icons.check_circle_rounded, size: 42), const SizedBox(height: 16), Text(cardSide == 0 ? 'Question' : 'Réponse', style: Theme.of(c).textTheme.labelLarge), const SizedBox(height: 8), Text(cardSide == 0 ? 'Quelle est l’idée essentielle de cette notion ?' : 'La réponse issue du contenu validé apparaît ici.', textAlign: TextAlign.center, style: Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)), const SizedBox(height: 16), Text('Touchez pour retourner', style: TextStyle(color: Theme.of(c).colorScheme.onSurfaceVariant))]))))),
    if (cardSide == 1) Padding(padding: const EdgeInsets.only(top: 14), child: Wrap(alignment: WrapAlignment.center, spacing: 8, runSpacing: 8, children: [for (final x in const ['À revoir','Difficile','Bien','Facile']) OutlinedButton(onPressed: () {}, child: Text(x))])),
  ]);

  Widget _quiz(BuildContext c) => _modeShell(c, 'Quiz', 'Question 3 sur 10 · maîtrise, pas simple lecture', Icons.quiz_rounded, [
    Text('Quelle proposition correspond le mieux au concept étudié ?', style: Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)), const SizedBox(height: 14),
    for (var i=0;i<4;i++) Padding(padding: const EdgeInsets.only(bottom: 9), child: InkWell(borderRadius: BorderRadius.circular(16), onTap: () => setState(() => quizChoice=i), child: Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(borderRadius: BorderRadius.circular(16), border: Border.all(color: quizChoice==i ? Theme.of(c).colorScheme.primary : Theme.of(c).colorScheme.outlineVariant, width: quizChoice==i ? 2 : 1)), child: Row(children: [CircleAvatar(radius: 15, child: Text(String.fromCharCode(65+i))), const SizedBox(width: 12), Expanded(child: Text('Proposition ${i+1}'))])))),
    SizedBox(width: double.infinity, child: FilledButton(onPressed: quizChoice<0 ? null : () {}, child: const Text('Valider ma réponse'))),
  ]);

  Widget _exercises(BuildContext c) => _modeShell(c, 'Exercices', 'Passe de la compréhension à l’application', Icons.calculate_rounded, [
    const _DelightCard(icon: Icons.track_changes_rounded, title: 'Objectif', text: 'Résoudre un exercice sans consulter la solution.'),
    const SizedBox(height: 10),
    SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: () {}, icon: const Icon(Icons.play_arrow_rounded), label: const Text('Commencer l’exercice'))),
  ]);

  Widget _modeShell(BuildContext c, String title, String subtitle, IconData icon, List<Widget> children) => ListView(padding: const EdgeInsets.fromLTRB(20, 22, 20, 110), children: [
    Row(children: [CircleAvatar(radius: 25, child: Icon(icon)), const SizedBox(width: 14), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: Theme.of(c).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)), Text(subtitle, style: TextStyle(color: Theme.of(c).colorScheme.onSurfaceVariant))]))]),
    const SizedBox(height: 24), ...children,
  ]);

  BoxDecoration _softBox(BuildContext c) => BoxDecoration(color: Theme.of(c).colorScheme.surfaceContainerLow, borderRadius: BorderRadius.circular(24), border: Border.all(color: Theme.of(c).colorScheme.outlineVariant.withValues(alpha: .7)));
}

class _SessionPill extends StatelessWidget { const _SessionPill({required this.minutes}); final int minutes; @override Widget build(BuildContext c) => Padding(padding: const EdgeInsets.symmetric(vertical: 10), child: Chip(avatar: const Icon(Icons.timer_outlined, size: 17), label: Text('$minutes min'))); }
class _Metric extends StatelessWidget { const _Metric({required this.icon, required this.value, required this.label}); final IconData icon; final String value,label; @override Widget build(BuildContext c)=>ListTile(contentPadding:EdgeInsets.zero,leading:Icon(icon),title:Text(value,style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),subtitle:Text(label)); }
class _DelightCard extends StatelessWidget { const _DelightCard({required this.icon,required this.title,required this.text}); final IconData icon; final String title,text; @override Widget build(BuildContext c)=>Card(child:Padding(padding:const EdgeInsets.all(18),child:Row(crossAxisAlignment:CrossAxisAlignment.start,children:[Icon(icon),const SizedBox(width:12),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(title,style:const TextStyle(fontWeight:FontWeight.w900)),const SizedBox(height:4),Text(text)]))]))); }
class _ExamCard extends StatelessWidget { const _ExamCard({required this.onTap}); final VoidCallback onTap; @override Widget build(BuildContext c)=>Container(padding:const EdgeInsets.all(16),decoration:BoxDecoration(gradient:LinearGradient(colors:[Theme.of(c).colorScheme.primaryContainer,Theme.of(c).colorScheme.secondaryContainer]),borderRadius:BorderRadius.circular(20)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Row(children:[Icon(Icons.event_available_rounded),SizedBox(width:8),Text('Exam Mode',style:TextStyle(fontWeight:FontWeight.w900))]),const SizedBox(height:7),const Text('Compte à rebours, priorités et objectif quotidien dans un seul parcours.'),const SizedBox(height:10),TextButton(onPressed:onTap,child:const Text('Configurer'))])); }
class _ToolDeck extends StatelessWidget { const _ToolDeck({required this.onMode}); final ValueChanged<int> onMode; @override Widget build(BuildContext c)=>Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Row(children:[Icon(Icons.auto_awesome_rounded),SizedBox(width:8),Text('Étudier autrement',style:TextStyle(fontWeight:FontWeight.w900))]),const SizedBox(height:12),Wrap(spacing:8,runSpacing:8,children:[ActionChip(avatar:const Icon(Icons.bolt_rounded),label:const Text('Révision rapide'),onPressed:()=>onMode(1)),ActionChip(avatar:const Icon(Icons.style_rounded),label:const Text('Flashcards'),onPressed:()=>onMode(2)),ActionChip(avatar:const Icon(Icons.quiz_rounded),label:const Text('Quiz'),onPressed:()=>onMode(3)),ActionChip(avatar:const Icon(Icons.calculate_rounded),label:const Text('Exercices'),onPressed:()=>onMode(4))])]))); }
class _MasteryJourney extends StatelessWidget { const _MasteryJourney({required this.progress}); final double progress; @override Widget build(BuildContext c)=>Semantics(label:'Progression de maîtrise',child:Card(child:Padding(padding:const EdgeInsets.all(18),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Row(children:[Text('Parcours de maîtrise',style:Theme.of(c).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900)),const Spacer(),Text('${(progress*100).round()}%',style:const TextStyle(fontWeight:FontWeight.w900))]),const SizedBox(height:12),TweenAnimationBuilder<double>(tween:Tween(begin:0,end:progress),duration:const Duration(milliseconds:650),builder:(c,v,_)=>LinearProgressIndicator(value:v,minHeight:8)),const SizedBox(height:12),const Wrap(spacing:8,runSpacing:8,children:[Chip(label:Text('✓ Lecture')),Chip(label:Text('✓ Étude')),Chip(label:Text('Pratique')),Chip(label:Text('Évaluation')),Chip(label:Text('Maîtrise'))])])))); }

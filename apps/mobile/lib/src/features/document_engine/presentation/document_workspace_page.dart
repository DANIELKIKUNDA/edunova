import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';

import '../../../core/di/providers.dart';
import '../../content/domain/personal_document.dart';
import '../domain/document_workspace.dart';
import 'widgets/local_document_surface.dart';

class DocumentWorkspacePage extends ConsumerStatefulWidget {
  const DocumentWorkspacePage({super.key, required this.documentId, this.initialPage});
  final String documentId;
  final int? initialPage;

  @override
  ConsumerState<DocumentWorkspacePage> createState() => _DocumentWorkspacePageState();
}

class _DocumentWorkspacePageState extends ConsumerState<DocumentWorkspacePage> {
  int _currentPage = 1;
  int _totalPages = 0;
  bool _toolsVisible = true;

  @override
  Widget build(BuildContext context) {
    final docAsync = ref.watch(personalDocumentByIdProvider(widget.documentId));
    return docAsync.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (error, _) => Scaffold(appBar: AppBar(), body: Center(child: Text('Impossible d’ouvrir le document.\n$error'))),
      data: (document) => document == null ? _missing(context) : _workspace(context, document),
    );
  }

  Widget _workspace(BuildContext context, PersonalDocument document) {
    final progress = ref.watch(documentProgressProvider(document.id)).valueOrNull;
    final annotations = ref.watch(documentAnnotationsProvider(document.id)).valueOrNull ?? const <DocumentAnnotation>[];
    final sections = ref.watch(documentSectionsProvider(document.id)).valueOrNull ?? const <DocumentSection>[];
    final bookmarked = annotations.any((a) => a.kind == DocumentAnnotationKind.bookmark && a.pageNumber == _currentPage);

    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.arrow_back_rounded)),
        titleSpacing: 0,
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(document.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
          Text(_currentPageLabel(progress), style: Theme.of(context).textTheme.labelSmall),
        ]),
        actions: [
          IconButton(tooltip: 'Rechercher', onPressed: () => _showSearch(context), icon: const Icon(Icons.search_rounded)),
          IconButton(tooltip: bookmarked ? 'Retirer le signet' : 'Ajouter un signet', onPressed: () => _toggleBookmark(document, bookmarked), icon: Icon(bookmarked ? Icons.bookmark_rounded : Icons.bookmark_border_rounded)),
          IconButton(tooltip: 'Outils', onPressed: () => setState(() => _toolsVisible = !_toolsVisible), icon: const Icon(Icons.tune_rounded)),
        ],
      ),
      body: Column(
        children: [
          if (_toolsVisible) _StudyToolbar(document: document, onOutline: () => _showOutline(context, sections), onAnnotations: () => _showAnnotations(context, annotations)),
          Expanded(
            child: LocalDocumentSurface(
              document: document,
              initialPage: widget.initialPage ?? progress?.pageNumber ?? 1,
              onPageChanged: (page, total) {
                setState(() { _currentPage = page; _totalPages = total; });
                _saveProgress(document.id, page, total);
              },
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 8, 14, 12),
          child: Row(children: [
            Expanded(child: _QuickAction(icon: Icons.auto_awesome_rounded, label: 'Résumé', onTap: () => _comingSoon('Résumé intelligent'))),
            const SizedBox(width: 8),
            Expanded(child: _QuickAction(icon: Icons.graphic_eq_rounded, label: 'Audio', onTap: () => _comingSoon('Résumé audio'))),
            const SizedBox(width: 8),
            Expanded(child: _QuickAction(icon: Icons.quiz_rounded, label: 'Quiz', onTap: () => _comingSoon('Quiz du chapitre'))),
            const SizedBox(width: 8),
            Expanded(child: _QuickAction(icon: Icons.psychology_alt_rounded, label: 'Assistant', onTap: () => context.push('/assistant?documentId=${document.id}'))),
          ]),
        ),
      ),
    );
  }

  Scaffold _missing(BuildContext context) => Scaffold(appBar: AppBar(), body: const Center(child: Text('Document introuvable.')));

  String _currentPageLabel(ReadingProgress? progress) {
    final total = _totalPages > 0 ? _totalPages : (progress?.totalPages ?? 0);
    return total > 0 ? 'Page $_currentPage / $total · lecture privée' : 'Lecture privée';
  }

  Future<void> _saveProgress(String id, int page, int total) async {
    await ref.read(documentWorkspaceRepositoryProvider).saveProgress(ReadingProgress(
      documentId: id,
      pageNumber: page,
      pageProgress: 0,
      totalPages: total,
      lastOpenedAt: DateTime.now(),
      secondsSpent: 0,
    ));
  }

  Future<void> _toggleBookmark(PersonalDocument document, bool bookmarked) async {
    final repo = ref.read(documentWorkspaceRepositoryProvider);
    final items = ref.read(documentAnnotationsProvider(document.id)).valueOrNull ?? const <DocumentAnnotation>[];
    DocumentAnnotation? existing;
    for (final item in items) {
      if (item.kind == DocumentAnnotationKind.bookmark && item.pageNumber == _currentPage) {
        existing = item;
        break;
      }
    }
    if (bookmarked && existing != null) {
      await repo.deleteAnnotation(existing.id);
      return;
    }
    final now = DateTime.now();
    await repo.saveAnnotation(DocumentAnnotation(
      id: const Uuid().v4(), documentId: document.id, kind: DocumentAnnotationKind.bookmark,
      pageNumber: _currentPage, createdAt: now, updatedAt: now,
    ));
  }

  void _showOutline(BuildContext context, List<DocumentSection> sections) {
    showModalBottomSheet<void>(context: context, isScrollControlled: true, showDragHandle: true, builder: (_) => FractionallySizedBox(
      heightFactor: .82,
      child: sections.isEmpty
          ? const _EmptyPanel(icon: Icons.account_tree_outlined, title: 'Sommaire en préparation', body: 'Le moteur documentaire construira ici les chapitres et sous-chapitres détectés.')
          : ListView.builder(padding: const EdgeInsets.fromLTRB(18, 8, 18, 24), itemCount: sections.length, itemBuilder: (_, index) {
              final item = sections[index];
              return ListTile(contentPadding: EdgeInsets.only(left: (item.level - 1) * 16.0), title: Text(item.title, style: const TextStyle(fontWeight: FontWeight.w800)), subtitle: Text('Pages ${item.startPage}–${item.endPage}'), trailing: const Icon(Icons.chevron_right_rounded));
            }),
    ));
  }

  void _showAnnotations(BuildContext context, List<DocumentAnnotation> annotations) {
    showModalBottomSheet<void>(context: context, isScrollControlled: true, showDragHandle: true, builder: (_) => FractionallySizedBox(
      heightFactor: .78,
      child: annotations.isEmpty
          ? const _EmptyPanel(icon: Icons.bookmarks_outlined, title: 'Aucune annotation', body: 'Ajoute un signet ou marque une page à revoir pendant ta lecture.')
          : ListView(padding: const EdgeInsets.fromLTRB(18, 8, 18, 24), children: annotations.map((a) => ListTile(leading: Icon(_annotationIcon(a.kind)), title: Text('Page ${a.pageNumber}'), subtitle: a.note == null ? null : Text(a.note!), trailing: const Icon(Icons.more_horiz_rounded))).toList()),
    ));
  }

  void _showSearch(BuildContext context) {
    showModalBottomSheet<void>(context: context, isScrollControlled: true, showDragHandle: true, builder: (_) => Padding(
      padding: EdgeInsets.fromLTRB(18, 8, 18, 18 + MediaQuery.viewInsetsOf(context).bottom),
      child: const Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text('Rechercher dans le document', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
        SizedBox(height: 12),
        TextField(autofocus: true, decoration: InputDecoration(prefixIcon: Icon(Icons.search_rounded), hintText: 'Mot, notion, formule…')),
        SizedBox(height: 12),
        Text('La recherche plein texte sera alimentée par les chunks locaux du moteur documentaire.'),
      ]),
    ));
  }

  IconData _annotationIcon(DocumentAnnotationKind kind) => switch (kind) {
    DocumentAnnotationKind.bookmark => Icons.bookmark_rounded,
    DocumentAnnotationKind.highlight => Icons.format_color_fill_rounded,
    DocumentAnnotationKind.note => Icons.sticky_note_2_rounded,
    DocumentAnnotationKind.review => Icons.refresh_rounded,
  };

  void _comingSoon(String feature) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$feature est branché sur le pipeline documentaire du prochain sous-lot.')));
}

class _StudyToolbar extends StatelessWidget {
  const _StudyToolbar({required this.document, required this.onOutline, required this.onAnnotations});
  final PersonalDocument document;
  final VoidCallback onOutline;
  final VoidCallback onAnnotations;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.fromLTRB(14, 8, 14, 10),
    decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Theme.of(context).colorScheme.outlineVariant.withValues(alpha: .6)))),
    child: Row(children: [
      Expanded(child: OutlinedButton.icon(onPressed: onOutline, icon: const Icon(Icons.account_tree_rounded), label: const Text('Chapitres'))),
      const SizedBox(width: 8),
      Expanded(child: OutlinedButton.icon(onPressed: onAnnotations, icon: const Icon(Icons.bookmarks_rounded), label: const Text('Mes repères'))),
      const SizedBox(width: 8),
      IconButton.filledTonal(onPressed: () {}, tooltip: 'À revoir', icon: const Icon(Icons.flag_rounded)),
    ]),
  );
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => InkWell(borderRadius: BorderRadius.circular(16), onTap: onTap, child: Padding(
    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 3),
    child: Column(mainAxisSize: MainAxisSize.min, children: [Icon(icon), const SizedBox(height: 4), Text(label, maxLines: 1, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800))]),
  ));
}

class _EmptyPanel extends StatelessWidget {
  const _EmptyPanel({required this.icon, required this.title, required this.body});
  final IconData icon; final String title; final String body;
  @override
  Widget build(BuildContext context) => Center(child: Padding(padding: const EdgeInsets.all(32), child: Column(mainAxisSize: MainAxisSize.min, children: [
    Icon(icon, size: 42), const SizedBox(height: 14), Text(title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)), const SizedBox(height: 8), Text(body, textAlign: TextAlign.center),
  ])));
}

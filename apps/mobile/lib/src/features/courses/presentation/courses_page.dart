import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../../content/domain/personal_document.dart';
import '../../library/domain/library.dart';
import 'import_document_sheet.dart';

class CoursesPage extends ConsumerStatefulWidget {
  const CoursesPage({super.key});

  @override
  ConsumerState<CoursesPage> createState() => _CoursesPageState();
}

class _CoursesPageState extends ConsumerState<CoursesPage> {
  int _segment = 0;
  bool _refreshing = false;
  String _query = '';
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    Future.microtask(_refreshCatalogSilently);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _refreshCatalogSilently() async {
    if (_refreshing) return;
    setState(() => _refreshing = true);
    try {
      final profile = await ref.read(academicProfileRepositoryProvider).getActive();
      await ref.read(refreshLibraryCatalogProvider)(
        facultyDomain: profile?.faculty,
        program: profile?.program,
        level: profile?.level,
        semester: profile?.semester,
      );
    } catch (_) {
      // Offline-first: keep cached catalog when network/auth is unavailable.
    } finally {
      if (mounted) setState(() => _refreshing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mes cours'),
        actions: [
          if (_refreshing) const Padding(padding: EdgeInsets.all(16), child: SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))),
          IconButton(onPressed: _refreshCatalogSilently, icon: const Icon(Icons.refresh_rounded)),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _openImport,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Ajouter'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 120),
        children: [
          SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 0, label: Text('Cours EduNova'), icon: Icon(Icons.school_rounded)),
              ButtonSegment(value: 1, label: Text('Mes documents'), icon: Icon(Icons.folder_copy_rounded)),
            ],
            selected: {_segment},
            onSelectionChanged: (value) => setState(() => _segment = value.first),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _searchController,
            onChanged: (value) => setState(() => _query = value.trim().toLowerCase()),
            decoration: InputDecoration(
              hintText: _segment == 0 ? 'Rechercher un cours, programme, niveau…' : 'Rechercher dans mes documents…',
              prefixIcon: const Icon(Icons.search_rounded),
              suffixIcon: _query.isEmpty
                  ? null
                  : IconButton(
                      tooltip: 'Effacer',
                      onPressed: () {
                        _searchController.clear();
                        setState(() => _query = '');
                      },
                      icon: const Icon(Icons.close_rounded),
                    ),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          if (_segment == 0) _edunovaCourses(context) else _personalDocuments(),
        ],
      ),
    );
  }

  Widget _edunovaCourses(BuildContext context) {
    final courses = ref.watch(libraryCoursesProvider);
    return courses.when(
      loading: () => const Padding(padding: EdgeInsets.all(32), child: Center(child: CircularProgressIndicator())),
      error: (error, _) => _emptyState('Catalogue indisponible', 'EduNova utilisera le dernier catalogue local dès qu’il est disponible.\n$error', Icons.cloud_off_rounded),
      data: (items) {
        final filtered = items.where((course) {
          if (_query.isEmpty) return true;
          return '${course.title} ${course.program} ${course.level} ${course.semester} ${course.facultyDomain} ${course.description}'
              .toLowerCase()
              .contains(_query);
        }).toList(growable: true)
          ..sort((a,b){
            if(a.followed!=b.followed) return a.followed ? -1 : 1;
            return a.title.compareTo(b.title);
          });
        if (items.isEmpty) {
          return _emptyState('Aucun cours EduNova pour ce parcours', 'Tu peux déjà importer tes propres documents. Le catalogue commun se remplira progressivement.', Icons.school_outlined);
        }
        if (filtered.isEmpty) {
          return _emptyState('Aucun résultat', 'Essaie un autre nom de cours, programme ou niveau.', Icons.search_off_rounded);
        }
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _catalogHeader(filtered.length),
            const SizedBox(height: 10),
            ...filtered.map(_libraryCourseCard),
          ],
        );
      },
    );
  }

  Widget _catalogHeader(int count) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
        child: Row(
          children: [
            const Icon(Icons.auto_awesome_rounded),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Bibliothèque EduNova', style: TextStyle(fontWeight: FontWeight.w900)),
                  Text('$count cours disponible${count > 1 ? 's' : ''} · cache hors connexion'),
                ],
              ),
            ),
            if (_refreshing) const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)),
          ],
        ),
      ),
    );
  }

  Widget _libraryCourseCard(LibraryCourseView course) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Card(
        child: ListTile(
          onTap: () => context.push('/library/${course.id}?title=${Uri.encodeComponent(course.title)}'),
          contentPadding: const EdgeInsets.all(16),
          leading: CircleAvatar(child: Icon(course.premiumRequired ? Icons.workspace_premium_rounded : Icons.menu_book_rounded)),
          title: Text(course.title, style: const TextStyle(fontWeight: FontWeight.w800)),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 5),
            child: Text('${course.program} · ${course.level} · ${course.semester}${course.premiumRequired ? ' · Premium' : ''}'),
          ),
          trailing: Row(mainAxisSize:MainAxisSize.min,children:[
            IconButton(
              tooltip: course.followed ? 'Retirer de Mes cours suivis' : 'Suivre ce cours',
              onPressed: () async => ref.read(libraryLocalRepositoryProvider).setCourseFollowed(course.id,!course.followed),
              icon: Icon(course.followed ? Icons.bookmark_rounded : Icons.bookmark_border_rounded),
            ),
            if(course.premiumRequired) const Tooltip(message:'Contenu Premium',child:Icon(Icons.workspace_premium_rounded)) else const Icon(Icons.chevron_right_rounded),
          ]),
        ),
      ),
    );
  }

  Widget _personalDocuments() {
    final docs = ref.watch(personalDocumentsProvider);
    return docs.when(
      loading: () => const Padding(padding: EdgeInsets.all(32), child: Center(child: CircularProgressIndicator())),
      error: (error, _) => _emptyState('Impossible de charger la bibliothèque', error.toString(), Icons.error_outline_rounded),
      data: (items) {
        final filtered = items.where((document) {
          if (_query.isEmpty) return true;
          return '${document.title} ${document.courseName ?? ''} ${_label(document.type)}'.toLowerCase().contains(_query);
        }).toList(growable: false);
        if (items.isEmpty) {
          return _emptyState(
            'Ta bibliothèque est encore vide',
            'Ajoute un PDF, une photo d’interrogation, un examen ou un exercice. Les fichiers personnels restent locaux.',
            Icons.folder_open_rounded,
          );
        }
        if (filtered.isEmpty) {
          return _emptyState('Aucun résultat', 'Aucun document personnel ne correspond à cette recherche.', Icons.search_off_rounded);
        }
        return Column(children: filtered.map(_documentCard).toList(growable: false));
      },
    );
  }

  Widget _documentCard(PersonalDocument document) {
    final icon = document.isImage ? Icons.image_rounded : Icons.picture_as_pdf_rounded;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Card(
        child: ListTile(
          onTap: () => context.push('/documents/${document.id}'),
          contentPadding: const EdgeInsets.all(16),
          leading: CircleAvatar(child: Icon(icon)),
          title: Text(document.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800)),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 5),
            child: Text('${_label(document.type)} · ${(document.sizeBytes / 1024 / 1024).toStringAsFixed(1)} Mo${document.courseName == null ? '' : ' · ${document.courseName}'}'),
          ),
          trailing: const Icon(Icons.lock_rounded, size: 18),
        ),
      ),
    );
  }

  Widget _emptyState(String title, String body, IconData icon) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          children: [
            CircleAvatar(radius: 30, child: Icon(icon, size: 30)),
            const SizedBox(height: 16),
            Text(title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            Text(body, textAlign: TextAlign.center),
            const SizedBox(height: 18),
            FilledButton.icon(onPressed: _openImport, icon: const Icon(Icons.add_rounded), label: const Text('Ajouter un document')),
          ],
        ),
      ),
    );
  }

  Future<void> _openImport() async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: false,
      builder: (_) => const ImportDocumentSheet(),
    );
  }

  String _label(PersonalDocumentType type) => switch (type) {
        PersonalDocumentType.course => 'Cours',
        PersonalDocumentType.interrogation => 'Interrogation',
        PersonalDocumentType.exam => 'Examen',
        PersonalDocumentType.exercise => 'Exercice',
        PersonalDocumentType.notes => 'Notes',
        PersonalDocumentType.other => 'Autre',
      };
}

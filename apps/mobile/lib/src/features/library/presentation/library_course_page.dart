import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../../delivery/presentation/offline_resource_tile.dart';
import '../domain/library.dart';

class LibraryCoursePage extends ConsumerStatefulWidget {
  const LibraryCoursePage({super.key, required this.courseId, required this.title});
  final String courseId;
  final String title;

  @override
  ConsumerState<LibraryCoursePage> createState() => _LibraryCoursePageState();
}

class _LibraryCoursePageState extends ConsumerState<LibraryCoursePage> {
  bool loading = true;
  bool downloading = false;
  String? error;
  String? versionId;
  LibraryVersionView? version;

  @override
  void initState() {
    super.initState();
    Future.microtask(_load);
  }

  Future<void> _load() async {
    if (mounted) setState(() { loading = true; error = null; });
    try {
      final manifest = await ref.read(libraryRemoteGatewayProvider).loadManifest(widget.courseId);
      await ref.read(libraryLocalRepositoryProvider).saveManifest(manifest);
      if (!mounted) return;
      setState(() {
        versionId = manifest.version.id;
        version = manifest.version;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = '$e';
        loading = false;
      });
    }
  }

  Future<void> _downloadCourse() async {
    if (downloading || loading || versionId == null) return;
    setState(() => downloading = true);
    try {
      final count = await ref.read(queueCourseOfflineProvider).call(widget.courseId, immediate: 2);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(count == 0 ? 'Aucune ressource hors ligne disponible.' : '$count ressource(s) ajoutée(s) au hors connexion.')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Impossible : $e')));
    } finally {
      if (mounted) setState(() => downloading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final resources = versionId == null ? null : ref.watch(libraryResourcesProvider(versionId!));
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(18, 10, 18, 120),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(widget.title, style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  Text(
                    version == null
                        ? 'Cours EduNova versionné · ressources protégées · manifeste vérifié'
                        : 'Version ${version!.label}${version!.academicYear == null ? '' : ' · ${version!.academicYear}'}',
                  ),
                  if (version != null && version!.changelog.trim().isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(version!.changelog, style: Theme.of(context).textTheme.bodySmall),
                  ],
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      FilledButton.icon(
                        onPressed: () => context.push('/study/${widget.courseId}?title=${Uri.encodeComponent(widget.title)}'),
                        icon: const Icon(Icons.school_rounded),
                        label: const Text('Étudier ce cours'),
                      ),
                      FilledButton.tonalIcon(
                        onPressed: loading || downloading || versionId == null ? null : _downloadCourse,
                        icon: downloading ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.download_for_offline_rounded),
                        label: Text(downloading ? 'Téléchargement en cours…' : 'Télécharger le cours'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          Text('Ressources', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          if (loading) const LinearProgressIndicator(),
          if (error != null) Card(child: ListTile(leading: const Icon(Icons.error_outline), title: const Text('Chargement du cours impossible'), subtitle: Text(error!), trailing: TextButton(onPressed: loading ? null : _load, child: const Text('Réessayer')))),
          if (resources != null)
            resources.when(
              loading: () => const LinearProgressIndicator(),
              error: (e, _) => Text('$e'),
              data: (items) => Column(
                children: items
                    .map(
                      (resource) => Card(
                        child: ListTile(
                          leading: Icon(resource.access == 'locked' ? Icons.lock_rounded : Icons.description_outlined),
                          title: Text(resource.title),
                          subtitle: Text('${resource.kind}${resource.offlineAllowed ? ' · hors ligne autorisé' : ''}'),
                          trailing: OfflineResourceTile(courseId: widget.courseId, resource: resource),
                        ),
                      ),
                    )
                    .toList(growable: false),
              ),
            ),
        ],
      ),
    );
  }
}

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/di/providers.dart';
import '../infrastructure/campus_services_gateway.dart';

/// Alumni profiles are opt-in and only institution-verified + consenting
/// profiles appear in the network directory. No contacts exposed by default.
class CampusAlumniPage extends ConsumerStatefulWidget {
  const CampusAlumniPage({super.key, required this.institutionId});
  final String institutionId;
  @override
  ConsumerState<CampusAlumniPage> createState() => _CampusAlumniState();
}

class _CampusAlumniState extends ConsumerState<CampusAlumniPage>
    with WidgetsBindingObserver {
  Map<String, dynamic>? _mine;
  List<Map<String, dynamic>> _directory = [], _pending = [], _opportunities = [];
  bool _loading = true, _busy = false, _admin = false, _canApply = false;
  String? _error;
  int _revision = 0;
  CampusServicesGateway get _api => ref.read(campusServicesGatewayProvider);

  @override
  void initState() { super.initState(); WidgetsBinding.instance.addObserver(this); _reload(); }
  @override
  void dispose() { ++_revision; WidgetsBinding.instance.removeObserver(this); super.dispose(); }
  @override
  void didUpdateWidget(covariant CampusAlumniPage old) {
    super.didUpdateWidget(old);
    if (old.institutionId != widget.institutionId) _reload();
  }
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) { _reload(); return; }
    ++_revision;
    if (mounted) setState(() { _mine = null; _directory = []; _pending = [];
      _opportunities = []; _admin = false; _canApply = false; _loading = true; });
  }
  Future<void> _reload() async {
    final req = ++_revision;
    setState(() { _mine = null; _directory = []; _pending = [];
      _opportunities = []; _admin = false; _canApply = false; _loading = true; _error = null; });
    try {
      final institutions = await _api.institutions();
      if (!mounted || req != _revision) return;
      final matches = institutions.where((row) =>
        row['institution'] is Map && (row['institution'] as Map)['id'] == widget.institutionId).toList();
      final role = matches.length == 1 && matches.single['membership'] is Map &&
        (matches.single['membership'] as Map)['state'] == 'active'
          ? (matches.single['membership'] as Map)['role']?.toString() : null;
      final admin = const {'owner','rector','admin','academic_admin'}.contains(role);
      final mine = await _api.alumniMe(widget.institutionId);
      if (!mounted || req != _revision) return;
      final directory = await _api.alumniDirectory(widget.institutionId);
      if (!mounted || req != _revision) return;
      final opportunities = await _api.alumniOpportunities(widget.institutionId);
      if (!mounted || req != _revision) return;
      final pending = admin ? await _api.alumniPending(widget.institutionId)
          : <Map<String, dynamic>>[];
      if (!mounted || req != _revision) return;
      if (directory.any((r) => r['status'] != 'verified' || r['visible'] != true)) {
        throw const FormatException('Publication Alumni non vérifiée');
      }
      setState(() { _mine = mine; _directory = directory; _opportunities = opportunities;
        _pending = pending; _admin = admin; _canApply = role != null; _loading = false; });
    } catch (e) {
      if (!mounted || req != _revision) return;
      setState(() { _mine = null; _directory = []; _pending = []; _opportunities = [];
        _admin = false; _canApply = false; _loading = false;
        _error = e is DioException && e.response?.statusCode == 403
          ? 'Vous ne possédez pas de droit d’accès Alumni pour cette université.'
          : 'Impossible de charger le réseau Alumni.'; });
    }
  }

  Future<void> _run(Future<void> Function() action) async {
    if (_busy) return;
    setState(() => _busy = true);
    try { await action(); if (mounted) await _reload(); }
    catch (e) {
      if (!mounted) return;
      if (e is DioException && (e.response?.statusCode == 401 || e.response?.statusCode == 403)) {
        await _reload();
      }
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Opération refusée ou version expirée. Actualisez vos données.')));
    } finally { if (mounted) setState(() => _busy = false); }
  }

  Future<void> _edit() async {
    final name = TextEditingController(text: (_mine?['display_name'] ?? '').toString());
    final program = TextEditingController(text: (_mine?['program_name'] ?? '').toString());
    final year = TextEditingController(text: (_mine?['graduation_year'] ?? '').toString());
    final headline = TextEditingController(text: (_mine?['headline'] ?? '').toString());
    var visible = _mine?['visible'] == true;
    try {
      final values = await showDialog<Map<String, dynamic>>(context: context,
        builder: (ctx) => StatefulBuilder(builder: (ctx, update) => AlertDialog(
          title: const Text('Demande de profil ancien étudiant'),
          content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
            TextField(controller: name, decoration: const InputDecoration(labelText: 'Nom affiché')),
            TextField(controller: program, decoration: const InputDecoration(labelText: 'Formation / filière')),
            TextField(controller: year, keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Année de diplôme')),
            TextField(controller: headline, decoration: const InputDecoration(labelText: 'Activité professionnelle')),
            SwitchListTile(title: const Text('Apparaître dans l’annuaire après vérification'),
              value: visible, onChanged: (v) => update(() => visible = v)),
            const Text('L’établissement vérifie manuellement votre diplôme. Les données ne seront pas publiques avant approbation.'),
          ])),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(onPressed: () {
              final y = int.tryParse(year.text);
              if (y == null || y < 1950 || y > DateTime.now().year ||
                  name.text.trim().length < 2 || program.text.trim().length < 2) return;
              Navigator.pop(ctx, {'name': name.text.trim(), 'program': program.text.trim(),
                'year': y, 'headline': headline.text.trim(), 'visible': visible});
            }, child: const Text('Soumettre')),
          ],
        )));
      if (values == null || !mounted) return;
      await _run(() async { await _api.applyAlumni(widget.institutionId,
        name: values['name'] as String, program: values['program'] as String,
        year: values['year'] as int, headline: values['headline'] as String,
        visible: values['visible'] as bool, version: (_mine?['row_version'] ?? 0) as int); });
    } finally { name.dispose(); program.dispose(); year.dispose(); headline.dispose(); }
  }

  Future<void> _decide(Map<String, dynamic> row, String decision) async {
    final reference = TextEditingController();
    try {
      final proof = await showDialog<String>(context: context, builder: (ctx) => AlertDialog(
        title: Text(decision == 'verified' ? 'Valider le diplôme' : 'Rejeter la demande'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('Référence interne du dossier contrôlé (non publiée)'),
          TextField(controller: reference, decoration: const InputDecoration(labelText: 'Référence de vérification')),
        ]),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          FilledButton(onPressed: () { if (reference.text.trim().length >= 6) {
            Navigator.pop(ctx, reference.text.trim()); } }, child: const Text('Confirmer'))]));
      if (proof == null || !mounted) return;
      await _run(() async { await _api.alumniDecide(widget.institutionId,
        row['id'] as String, row['row_version'] as int, decision, proof); });
    } finally { reference.dispose(); }
  }

  Future<void> _publish() async {
    final title = TextEditingController(), description = TextEditingController(),
        url = TextEditingController();
    try {
      final data = await showDialog<Map<String, String>>(context: context, builder: (ctx) => AlertDialog(
        title: const Text('Publier une opportunité'),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: title, decoration: const InputDecoration(labelText: 'Titre')),
          TextField(controller: description, maxLines: 3, decoration: const InputDecoration(labelText: 'Description')),
          TextField(controller: url, decoration: const InputDecoration(labelText: 'Lien HTTPS facultatif')),
        ])),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          FilledButton(onPressed: () {
            if (title.text.trim().length < 4 || description.text.trim().length < 10 ||
                (url.text.trim().isNotEmpty && !url.text.trim().startsWith('https://'))) return;
            Navigator.pop(ctx, {'title': title.text.trim(), 'description': description.text.trim(),
              'url': url.text.trim()});
          }, child: const Text('Publier'))],
      ));
      if (data == null || !mounted) return;
      await _run(() async { await _api.alumniPublishOpportunity(widget.institutionId,
        data['title']!, data['description']!, data['url']!); });
    } finally { title.dispose(); description.dispose(); url.dispose(); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('EduNova Alumni'), actions: [
      IconButton(onPressed: _busy ? null : _reload, icon: const Icon(Icons.refresh))]),
    body: _loading ? const Center(child: CircularProgressIndicator()) :
      _error != null ? Center(child: Text(_error!)) : ListView(padding: const EdgeInsets.all(16), children: [
        Card(child: ListTile(leading: const Icon(Icons.badge_outlined),
          title: Text(_mine == null ? 'Créer mon profil Alumni' :
            'Mon profil : ${_mine!['status']}'),
          subtitle: const Text('Publication volontaire après contrôle institutionnel'),
          trailing: _canApply ? FilledButton(onPressed: _busy ? null : _edit,
              child: const Text('Modifier')) : const Icon(Icons.lock_outline),)),
        const SizedBox(height: 18),
        Text('Anciens étudiants vérifiés', style: Theme.of(context).textTheme.titleLarge),
        if (_directory.isEmpty) const ListTile(title: Text('Aucun profil public vérifié')),
        for (final row in _directory) ListTile(
          leading: const Icon(Icons.school_outlined),
          title: Text((row['display_name'] ?? '').toString()),
          subtitle: Text('${row['program_name']} · ${row['graduation_year']}\n${row['headline']}'),
          isThreeLine: true),
        const SizedBox(height: 18),
        Text('Opportunités professionnelles', style: Theme.of(context).textTheme.titleLarge),
        if (_admin) Align(alignment: Alignment.centerLeft, child: OutlinedButton.icon(
          icon: const Icon(Icons.add), onPressed: _busy ? null : _publish,
          label: const Text('Publier une opportunité'))),
        if (_opportunities.isEmpty) const ListTile(title: Text('Aucune opportunité publiée')),
        for (final row in _opportunities) ListTile(
          title: Text((row['title'] ?? '').toString()),
          subtitle: Text('${row['description']}\n${row['application_url']}'),
          trailing: _admin ? IconButton(tooltip: 'Retirer cette offre',
            icon: const Icon(Icons.remove_circle_outline), onPressed: _busy ? null : () => _run(() async {
              await _api.alumniWithdrawOpportunity(widget.institutionId,
                row['id'] as String, row['row_version'] as int);
            })) : null),
        if (_admin) ...[
          const Divider(),
          Text('Dossiers à vérifier', style: Theme.of(context).textTheme.titleLarge),
          for (final row in _pending) ListTile(
            title: Text((row['display_name'] ?? '').toString()),
            subtitle: Text('${row['program_name']} · ${row['graduation_year']}'),
            trailing: Wrap(mainAxisSize: MainAxisSize.min, children: [
              IconButton(tooltip: 'Vérifier', icon: const Icon(Icons.verified_outlined),
                onPressed: _busy ? null : () => _decide(row, 'verified')),
              IconButton(tooltip: 'Rejeter', icon: const Icon(Icons.block_outlined),
                onPressed: _busy ? null : () => _decide(row, 'rejected')),
            ])),
        ],
        const SizedBox(height: 30),
        const Center(child: Text('From Volcano Tech')),
      ]),
  );
}

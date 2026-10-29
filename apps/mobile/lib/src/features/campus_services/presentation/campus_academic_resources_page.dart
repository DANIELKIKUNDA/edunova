import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/di/providers.dart';
import '../infrastructure/campus_services_gateway.dart';

/// Academic sessions and exams are NOT duplicated: calendar_event_id links the
/// canonical academic calendar to a campus physical room or laboratory.
class CampusAcademicResourcesPage extends ConsumerStatefulWidget {
  const CampusAcademicResourcesPage({super.key, required this.institutionId});
  final String institutionId;
  @override
  ConsumerState<CampusAcademicResourcesPage> createState() => _CampusAcademicResourcesState();
}

class _CampusAcademicResourcesState extends ConsumerState<CampusAcademicResourcesPage>
    with WidgetsBindingObserver {
  int _revision = 0;
  bool _loading = true, _busy = false;
  String? _error;
  List<Map<String, dynamic>> _rooms = [], _allocations = [], _teachings = [];
  Map<String, dynamic> _unassigned = {};
  CampusServicesGateway get _api => ref.read(campusServicesGatewayProvider);

  @override
  void initState() { super.initState(); WidgetsBinding.instance.addObserver(this); _reload(); }
  @override
  void dispose() { ++_revision; WidgetsBinding.instance.removeObserver(this); super.dispose(); }
  @override
  void didUpdateWidget(covariant CampusAcademicResourcesPage old) {
    super.didUpdateWidget(old);
    if (old.institutionId != widget.institutionId) _reload();
  }
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) { _reload(); return; }
    ++_revision;
    if (mounted) setState(() { _rooms = []; _allocations = []; _teachings = []; _unassigned = {}; _loading = true; });
  }

  Future<void> _reload() async {
    final request = ++_revision;
    setState(() { _rooms = []; _allocations = []; _teachings = []; _unassigned = {}; _loading = true; _error = null; });
    try {
      final rooms = await _api.resources(widget.institutionId);
      if (!mounted || request != _revision) return;
      final allocations = await _api.academicAllocations(widget.institutionId);
      if (!mounted || request != _revision) return;
      final teachings = await _api.teachingAllocations(widget.institutionId);
      if (!mounted || request != _revision) return;
      final unassigned = await _api.academicUnassigned(widget.institutionId);
      if (!mounted || request != _revision) return;
      if (unassigned['calendar'] is! List || unassigned['teaching'] is! List ||
          unassigned['calendar_count'] is! int || unassigned['teaching_count'] is! int) {
        throw const FormatException('Inventaire des séances incomplet');
      }
      final seen = <String>{};
      for (final row in allocations) {
        if (row['id'] is! String || !seen.add(row['id'] as String) ||
            row['calendar_event_id'] is! String || row['resource_id'] is! String) {
          throw const FormatException('Affectations académiques incohérentes');
        }
      }
      for (final row in teachings) {
        if (row['id'] is! String || !seen.add(row['id'] as String) ||
            row['teaching_session_id'] is! String || row['resource_id'] is! String) {
          throw const FormatException('Liaisons de séance incohérentes');
        }
      }
      setState(() { _rooms = rooms.where((row) =>
        const {'room','laboratory','library_space'}.contains(row['kind'])).toList();
        _allocations = allocations; _teachings = teachings;
        _unassigned = unassigned; _loading = false; });
    } catch (e) {
      if (!mounted || request != _revision) return;
      setState(() { _rooms = []; _allocations = []; _teachings = []; _unassigned = {}; _loading = false;
        _error = e is DioException && e.response?.statusCode == 403
          ? 'Accès administratif refusé.' : 'Impossible de consulter les affectations.'; });
    }
  }

  Future<void> _assign() async {
    if (_busy || _rooms.isEmpty) return;
    final candidates = <Map<String, String>>[
      for (final row in (_unassigned['calendar'] as List? ?? []))
        if (row is Map && row['id'] is String)
          {'id': row['id'] as String, 'kind': 'calendar',
            'label': (row['title'] ?? row['id']).toString()},
      for (final row in (_unassigned['teaching'] as List? ?? []))
        if (row is Map && row['id'] is String)
          {'id': row['id'] as String, 'kind': 'teaching',
            'label': (row['title'] ?? row['id']).toString()},
    ];
    if (candidates.isEmpty) return;
    String? selectedEvent = candidates.first['id'];
    var kind = candidates.first['kind']!;
    String? roomId = _rooms.first['id'] as String?;
    {
      final requested = await showDialog<Map<String, String>>(context: context,
        builder: (ctx) => StatefulBuilder(builder: (ctx, change) => AlertDialog(
          title: const Text('Affecter une salle à une séance'),
          content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Text('Sélectionnez une séance canonique non affectée. Aucun nouvel horaire n’est créé.'),
            DropdownButtonFormField<String>(initialValue: selectedEvent,
              isExpanded: true,
              items: candidates.map((c) => DropdownMenuItem(
                value: c['id'], child: Text('${c['kind']} · ${c['label']}',
                  overflow: TextOverflow.ellipsis))).toList(),
              onChanged: (v) => change(() { selectedEvent = v;
                kind = candidates.firstWhere((c) => c['id'] == v)['kind']!; })),
            DropdownButtonFormField<String>(initialValue: roomId,
              items: _rooms.map((r) => DropdownMenuItem(value: r['id'] as String,
                child: Text((r['name'] ?? r['code']).toString()))).toList(),
              onChanged: (v) => change(() => roomId = v)),
          ])),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(onPressed: () {
              if (selectedEvent == null || roomId == null) return;
              Navigator.pop(ctx, {'event': selectedEvent!, 'room': roomId!, 'kind': kind});
            }, child: const Text('Vérifier et affecter')),
          ],
        )));
      if (requested == null || !mounted) return;
      setState(() => _busy = true);
      try {
        if (requested['kind'] == 'teaching') {
          await _api.assignTeachingRoom(widget.institutionId,
            requested['event']!, requested['room']!);
        } else {
          await _api.assignAcademicRoom(widget.institutionId,
            requested['event']!, requested['room']!);
        }
        if (mounted) await _reload();
      } catch (e) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(
          e is DioException && e.response?.statusCode == 409
            ? 'Salle déjà occupée, réservée ou indisponible.' : 'Affectation impossible.')));
        if (e is DioException && (e.response?.statusCode == 401 || e.response?.statusCode == 403)) {
          if (mounted) await _reload();
        }
      } finally { if (mounted) setState(() => _busy = false); }
    }
  }

  Future<void> _release(Map<String, dynamic> row) async {
    if (_busy) return;
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Libérer cette salle ?'),
      content: const Text('Cette opération n’annule pas l’événement du calendrier.'),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Non')),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Libérer'))]));
    if (ok != true || !mounted) return;
    setState(() => _busy = true);
    try {
      if (row['teaching_session_id'] is String) {
        await _api.releaseTeachingRoom(widget.institutionId, row['id'] as String,
          row['row_version'] as int);
      } else {
        await _api.releaseAcademicRoom(widget.institutionId, row['id'] as String,
          row['row_version'] as int);
      }
      if (mounted) await _reload();
    } catch (_) { if (mounted) await _reload(); }
    finally { if (mounted) setState(() => _busy = false); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Salles et calendrier académique'), actions: [
      IconButton(onPressed: _busy ? null : _reload, icon: const Icon(Icons.refresh))]),
    floatingActionButton: _loading || _rooms.isEmpty ||
      ((_unassigned['calendar'] as List? ?? []).isEmpty &&
       (_unassigned['teaching'] as List? ?? []).isEmpty) ? null : FloatingActionButton.extended(
      onPressed: _busy ? null : _assign, icon: const Icon(Icons.add), label: const Text('Affecter')),
    body: _loading ? const Center(child: CircularProgressIndicator()) :
      _error != null ? Center(child: Text(_error!)) :
      ListView(children: [
        ListTile(leading: const Icon(Icons.rule_folder_outlined),
          title: const Text('Séances à rapprocher des salles'),
          subtitle: Text('Calendrier : ${_unassigned['calendar_count'] ?? '?'} · '
              'Enseignement : ${_unassigned['teaching_count'] ?? '?'}'
              '${_unassigned['truncated'] == true ? ' · Liste partielle' : ''}\n'
              'Les horaires sans liaison à une salle ne sont pas automatiquement protégés.'),
          isThreeLine: true),
        const ListTile(title: Text('Occupations académiques'),
          subtitle: Text('Références au calendrier ET aux séances existantes, sans emploi du temps parallèle.')),
        for (final row in [..._allocations, ..._teachings]) ListTile(
          leading: const Icon(Icons.class_outlined),
          title: Text((row['title'] ?? row['calendar_event_id']).toString()),
          subtitle: Text('${row['starts_at']} → ${row['ends_at']}\nSalle : ${row['resource_id']} · ${row['state']}'),
          isThreeLine: true,
          trailing: IconButton(tooltip: 'Libérer', onPressed: _busy ? null : () => _release(row),
            icon: const Icon(Icons.link_off))),
        if (_allocations.isEmpty && _teachings.isEmpty) const ListTile(title: Text('Aucune affectation enregistrée')),
        const SizedBox(height: 80),
      ]),
  );
}

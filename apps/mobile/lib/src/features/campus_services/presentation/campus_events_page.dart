import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../infrastructure/campus_services_gateway.dart';

/// Inscriptions aux événements du calendrier universitaire existant.
/// Les données privées sont vidées lors du changement d'université/session.
class CampusEventsPage extends ConsumerStatefulWidget {
  const CampusEventsPage({super.key, required this.institutionId});
  final String institutionId;

  @override
  ConsumerState<CampusEventsPage> createState() => _CampusEventsPageState();
}

class _CampusEventsPageState extends ConsumerState<CampusEventsPage>
    with WidgetsBindingObserver {
  List<Map<String, dynamic>> _events = [];
  String? _role, _error;
  bool _loading = true, _saving = false;
  int _revision = 0;

  CampusServicesGateway get _gateway => ref.read(campusServicesGatewayProvider);
  bool get _admin => const {'owner', 'rector', 'admin', 'academic_admin'}.contains(_role);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _reload();
  }

  @override
  void dispose() {
    ++_revision;
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant CampusEventsPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.institutionId != widget.institutionId) _reload();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _reload();
    } else {
      ++_revision;
      if (mounted) {
        setState(() {
        _events = [];
        _role = null;
        _loading = true;
      });
      }
    }
  }

  String _message(Object e) {
    if (e is DioException) {
      if (e.response?.statusCode == 403) return 'Accès universitaire refusé.';
      if (e.response?.statusCode == 401) return 'Session expirée.';
      if (e.response?.statusCode == 409) {
        return 'Places épuisées ou modification concurrente. Actualisez.';
      }
      return 'Événements momentanément indisponibles.';
    }
    return 'Impossible de consulter les événements.';
  }

  Future<void> _reload() async {
    final generation = ++_revision;
    if (!mounted) return;
    setState(() { _events = []; _role = null; _error = null; _loading = true; });
    try {
      final institutions = await _gateway.institutions();
      if (!mounted || generation != _revision) return;
      final mine = institutions.where((entry) {
        final institution = entry['institution'];
        return institution is Map && institution['id'] == widget.institutionId;
      }).toList();
      if (mine.length != 1 || mine.single['membership'] is! Map ||
          mine.single['institution'] is! Map) {
        throw const FormatException();
      }
      final membership = mine.single['membership'] as Map;
      final institution = mine.single['institution'] as Map;
      if (membership['state'] != 'active' || institution['state'] != 'active') {
        throw const FormatException();
      }
      final events = await _gateway.events(widget.institutionId);
      if (!mounted || generation != _revision) return;
      final ids = <String>{};
      for (final event in events) {
        if (event['id'] is! String || !ids.add(event['id'] as String)) {
          throw const FormatException('Événements dupliqués');
        }
      }
      setState(() { _events = events; _role = membership['role']?.toString(); _loading = false; });
    } catch (error) {
      if (!mounted || generation != _revision) return;
      setState(() { _events = []; _role = null; _error = _message(error); _loading = false; });
    }
  }

  Future<void> _execute(Future<void> Function() operation) async {
    if (_saving) return;
    final institution = widget.institutionId;
    final generation = _revision;
    setState(() => _saving = true);
    try {
      await operation();
      if (mounted && generation == _revision && institution == widget.institutionId) {
        await _reload();
      }
    } catch (error) {
      if (!mounted || generation != _revision) return;
      if (error is DioException &&
          (error.response?.statusCode == 401 || error.response?.statusCode == 403)) {
        await _reload();
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_message(error))));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<bool> _confirm(String text) async {
    return await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Confirmation'), content: Text(text),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx, false),
          child: const Text('Annuler')),
        FilledButton(onPressed: () => Navigator.pop(ctx, true),
          child: const Text('Confirmer'))],
    )) ?? false;
  }

  Future<void> _configure(Map<String, dynamic> event) async {
    if (!_admin) return;
    final controller = TextEditingController(
      text: '${event['registration_capacity'] ?? 0}');
    try {
      final count = await showDialog<int>(context: context, builder: (ctx) => AlertDialog(
        title: const Text('Nombre de places (0 = inscriptions fermées)'),
        content: TextField(controller: controller,
          decoration: const InputDecoration(labelText: 'Capacité 0 à 5000'),
          keyboardType: TextInputType.number),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx),
          child: const Text('Annuler')),
          FilledButton(onPressed: () {
            final n = int.tryParse(controller.text.trim());
            if (n != null && n >= 0 && n <= 5000) Navigator.pop(ctx, n);
          }, child: const Text('Enregistrer'))],
      ));
      if (count == null || !mounted) return;
      await _execute(() async { await _gateway.configureEventCapacity(
        widget.institutionId, event['id'] as String,
        event['row_version'] as int, count);
      });
    } finally {
      controller.dispose();
    }
  }

  Future<void> _create() async {
    if (!_admin) return;
    final title = TextEditingController();
    final details = TextEditingController();
    final location = TextEditingController();
    var date = DateTime.now().add(const Duration(days: 1));
    var time = const TimeOfDay(hour: 9, minute: 0);
    try {
      final confirmed = await showDialog<bool>(context: context, builder: (dialog) =>
        StatefulBuilder(builder: (ctx, update) => AlertDialog(
          title: const Text('Nouvel événement Campus'),
          content: SingleChildScrollView(child: Column(
            mainAxisSize: MainAxisSize.min, children: [
            TextField(controller: title, onChanged: (_) => update(() {}),
              decoration: const InputDecoration(labelText: 'Titre')),
            TextField(controller: details, decoration: const InputDecoration(labelText: 'Description')),
            TextField(controller: location, decoration: const InputDecoration(labelText: 'Lieu')),
            ListTile(title: Text('Date : ${date.day}/${date.month}/${date.year}'),
              onTap: () async {
                final d = await showDatePicker(context: ctx, initialDate: date,
                  firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 365)));
                if (d != null) update(() => date = d);
              }),
            ListTile(title: Text('Début : ${time.format(ctx)}'), onTap: () async {
              final t = await showTimePicker(context: ctx, initialTime: time);
              if (t != null) update(() => time = t);
            }),
          ])),
          actions: [TextButton(onPressed: () => Navigator.pop(ctx),
              child: const Text('Annuler')),
            FilledButton(onPressed: title.text.trim().isEmpty ? null : () => Navigator.pop(ctx, true),
              child: const Text('Créer'))],
        )));
      if (confirmed != true || !mounted || title.text.trim().isEmpty) return;
      final start = DateTime(date.year, date.month, date.day, time.hour, time.minute);
      if (!start.isAfter(DateTime.now())) return;
      await _execute(() async { await _gateway.publishCampusEvent(widget.institutionId,
        title: title.text.trim(), details: details.text.trim(),
        location: location.text.trim(), startsAt: start,
        endsAt: start.add(const Duration(hours: 2)));
      });
    } finally { title.dispose(); details.dispose(); location.dispose(); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Événements universitaires'), actions: [
      IconButton(onPressed: _saving ? null : _reload,
        icon: const Icon(Icons.refresh), tooltip: 'Actualiser'),
    ]),
    floatingActionButton: !_loading && _admin ? FloatingActionButton.extended(
      onPressed: _saving ? null : _create,
      icon: const Icon(Icons.add), label: const Text('Événement')) : null,
    body: _loading ? const Center(child: CircularProgressIndicator())
      : _error != null ? Center(child: Column(mainAxisSize: MainAxisSize.min,
        children: [Text(_error!), TextButton(onPressed: _reload, child: const Text('Réessayer'))]))
      : _events.isEmpty ? const Center(child: Text('Aucun événement accessible.'))
      : ListView(padding: const EdgeInsets.all(16), children: [
        const Text('Inscriptions limitées aux places configurées par votre université.'),
        for (final event in _events) Card(child: Padding(
          padding: const EdgeInsets.all(12), child: Column(
          crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('${event['title'] ?? ''}', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 6),
            Text('${event['starts_at'] ?? ''} · ${event['location'] ?? ''}'),
            if ((event['details']?.toString() ?? '').isNotEmpty) Text('${event['details']}'),
            Text('Statut : ${event['state'] ?? ''} · Inscriptions : '
              '${event['registrations_count'] ?? 0}/${event['registration_capacity'] ?? 0}'),
            if (event['my_registration'] is Map &&
                (event['my_registration'] as Map)['state'] == 'registered')
              const Text('Votre inscription est confirmée.'),
            Wrap(spacing: 8, children: [
              if (!_saving && _role != null && _role != 'auditor' &&
                  event['my_registration'] is Map &&
                  (event['my_registration'] as Map)['state'] == 'registered')
                OutlinedButton(onPressed: () async {
                  if (!await _confirm('Annuler votre inscription ?')) return;
                  final mine = event['my_registration'] as Map;
                  await _execute(() async { await _gateway.withdrawFromEvent(
                    widget.institutionId, event['id'] as String,
                    mine['row_version'] as int); });
                }, child: const Text('Se désinscrire')),
              if (!_saving && _role != null && _role != 'auditor' &&
                  event['registration_open'] == true &&
                  !(event['my_registration'] is Map &&
                    (event['my_registration'] as Map)['state'] == 'registered'))
                FilledButton(onPressed: () async {
                  if (!await _confirm('Confirmer votre inscription ?')) return;
                  await _execute(() async { await _gateway.registerForEvent(
                    widget.institutionId, event['id'] as String); });
                }, child: const Text('S’inscrire')),
              if (_admin && !_saving && event['state'] == 'scheduled')
                TextButton(onPressed: () => _configure(event),
                  child: const Text('Gérer les places')),
            ]),
          ]),
        )),
      ]),
  );
}

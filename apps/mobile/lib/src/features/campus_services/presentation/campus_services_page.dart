import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../infrastructure/campus_services_gateway.dart';

/// Phase 16: bookable resources. The API enforces tenant isolation and RBAC.
class CampusServicesPage extends ConsumerStatefulWidget {
  const CampusServicesPage({super.key, required this.institutionId});
  final String institutionId;

  @override
  ConsumerState<CampusServicesPage> createState() => _CampusServicesPageState();
}

class _CampusServicesPageState extends ConsumerState<CampusServicesPage>
    with WidgetsBindingObserver {
  List<Map<String, dynamic>> _resources = [], _bookings = [], _maintenance = [], _alerts = [];
  String? _error, _role;
  bool _loading = true, _saving = false;
  int _revision = 0;

  CampusServicesGateway get _api => ref.read(campusServicesGatewayProvider);
  bool get _admin => const {'owner', 'rector', 'admin', 'academic_admin'}.contains(_role);
  bool get _canReserve => _role != null && _role != 'auditor';

  @override
  void initState() { super.initState(); WidgetsBinding.instance.addObserver(this); _reload(); }
  @override
  void dispose() { ++_revision; WidgetsBinding.instance.removeObserver(this); super.dispose(); }

  @override
  void didUpdateWidget(covariant CampusServicesPage old) {
    super.didUpdateWidget(old);
    if (old.institutionId != widget.institutionId) _reload();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) { _reload(); return; }
    ++_revision;
    if (mounted) setState(() { _resources = []; _bookings = []; _maintenance = []; _alerts = []; _role = null; _loading = true; });
  }

  String _message(Object error) {
    if (error is DioException) {
      switch (error.response?.statusCode) {
        case 401: return 'Session expirée. Reconnectez-vous.';
        case 403: return 'Accès refusé ou permission révoquée.';
        case 409: return 'Conflit de réservation, maintenance ou version obsolète.';
        default: return 'Service Campus indisponible. Réessayez.';
      }
    }
    if (error is FormatException) return 'Réponse du service Campus invalide.';
    return 'Impossible de terminer cette opération.';
  }

  Future<void> _reload() async {
    final revision = ++_revision;
    setState(() { _loading = true; _error = null; _resources = []; _bookings = []; _maintenance = []; _alerts = []; _role = null; });
    try {
      final institutions = await _api.institutions();
      if (!mounted || revision != _revision) return;
      final matching = institutions.where((entry) {
        final institution = entry['institution'];
        return institution is Map && institution['id'] == widget.institutionId;
      }).toList();
      if (matching.length != 1) throw const FormatException('Université ambiguë');
      final membership = matching.single['membership'];
      final institution = matching.single['institution'];
      if (membership is! Map || membership['state'] != 'active' ||
          institution is! Map || institution['state'] != 'active') {
        throw const FormatException('Accès institutionnel inactif');
      }
      final role = membership['role']?.toString() ?? '';
      final resources = await _api.resources(widget.institutionId);
      if (!mounted || revision != _revision) return;
      final bookings = await _api.bookings(widget.institutionId);
      if (!mounted || revision != _revision) return;
      final maintenance = await _api.maintenanceTickets(widget.institutionId);
      if (!mounted || revision != _revision) return;
      final alerts = await _api.campusAlerts(widget.institutionId);
      if (!mounted || revision != _revision) return;
      final known = <String>{};
      for (final item in resources) {
        final id = item['id'];
        if (id is! String || !known.add(id)) throw const FormatException('Références en double');
      }
      final knownTickets = <String>{};
      for (final item in maintenance) {
        final id = item['id'];
        if (id is! String || !knownTickets.add(id)) {
          throw const FormatException('Signalements de maintenance dupliqués');
        }
      }
      setState(() { _resources = resources; _bookings = bookings;
        _maintenance = maintenance; _alerts = alerts; _role = role; _loading = false; });
    } catch (error) {
      if (!mounted || revision != _revision) return;
      setState(() { _resources = []; _bookings = []; _maintenance = []; _alerts = []; _role = null;
        _loading = false; _error = _message(error); });
    }
  }

  Future<void> _run(Future<void> Function() action) async {
    if (_saving) return;
    setState(() => _saving = true);
    try {
      await action();
      if (mounted) await _reload();
    } catch (error) {
      if (!mounted) return;
      if (error is DioException && (error.response?.statusCode == 401 ||
          error.response?.statusCode == 403)) {
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

  Future<void> _register() async {
    if (!_admin) return;
    final code = TextEditingController(), name = TextEditingController(),
        location = TextEditingController(), capacity = TextEditingController(text: '1');
    String kind = 'room';
    try {
      final requested = await showDialog<Map<String, dynamic>>(context: context, builder: (ctx) =>
        StatefulBuilder(builder: (ctx, update) => AlertDialog(
          title: const Text('Nouvelle ressource Campus'),
          content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
            DropdownButtonFormField<String>(initialValue: kind,
              items: const [
                DropdownMenuItem(value: 'room', child: Text('Salle')),
                DropdownMenuItem(value: 'laboratory', child: Text('Laboratoire')),
                DropdownMenuItem(value: 'equipment', child: Text('Équipement')),
                DropdownMenuItem(value: 'library_space', child: Text('Espace bibliothèque')),
              ], onChanged: (v) { if (v != null) update(() => kind = v); }),
            TextField(controller: code, decoration: const InputDecoration(labelText: 'Code unique')),
            TextField(controller: name, decoration: const InputDecoration(labelText: 'Nom')),
            TextField(controller: location, decoration: const InputDecoration(labelText: 'Emplacement')),
            TextField(controller: capacity, keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Capacité')),
          ])),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(onPressed: () {
              final amount = int.tryParse(capacity.text);
              if (code.text.trim().isEmpty || name.text.trim().isEmpty ||
                  amount == null || amount < 1 || amount > 5000) {
                return;
              }
              Navigator.pop(ctx, {'kind': kind, 'code': code.text.trim(),
                'name': name.text.trim(), 'location': location.text.trim(), 'capacity': amount});
            }, child: const Text('Enregistrer')),
          ],
        )));
      if (requested == null || !mounted) return;
      await _run(() async { await _api.register(widget.institutionId,
          kind: requested['kind'] as String, code: requested['code'] as String,
          name: requested['name'] as String, location: requested['location'] as String,
          capacity: requested['capacity'] as int); });
    } finally { code.dispose(); name.dispose(); location.dispose(); capacity.dispose(); }
  }

  Future<void> _reserve(Map<String, dynamic> resource) async {
    if (!_canReserve) return;
    final purpose = TextEditingController();
    var date = DateTime.now().add(const Duration(days: 1));
    var time = const TimeOfDay(hour: 9, minute: 0);
    var hours = 2;
    try {
      final requested = await showDialog<Map<String, dynamic>>(context: context,
          builder: (dialogCtx) => StatefulBuilder(builder: (ctx, update) => AlertDialog(
        title: Text('Réserver ${resource['name'] ?? 'une ressource'}'),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: purpose, decoration: const InputDecoration(labelText: 'Motif')),
          ListTile(title: Text('Date : ${date.day}/${date.month}/${date.year}'),
            trailing: const Icon(Icons.calendar_month), onTap: () async {
              final chosen = await showDatePicker(context: ctx, initialDate: date,
                firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 89)));
              if (chosen != null) update(() => date = chosen);
            }),
          ListTile(title: Text('Début : ${time.format(ctx)}'),
            trailing: const Icon(Icons.schedule), onTap: () async {
              final chosen = await showTimePicker(context: ctx, initialTime: time);
              if (chosen != null) update(() => time = chosen);
            }),
          DropdownButtonFormField<int>(initialValue: hours,
            decoration: const InputDecoration(labelText: 'Durée'),
            items: [1,2,3,4,5,6,7,8].map((h) => DropdownMenuItem(value: h,
              child: Text('$h h'))).toList(),
            onChanged: (h) { if (h != null) update(() => hours = h); }),
        ])),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
          FilledButton(onPressed: () {
            if (purpose.text.trim().isEmpty) return;
            final start = DateTime(date.year, date.month, date.day, time.hour, time.minute);
            if (!start.isAfter(DateTime.now())) return;
            Navigator.pop(ctx, {'purpose': purpose.text.trim(), 'start': start,
              'end': start.add(Duration(hours: hours))});
          }, child: const Text('Confirmer')),
        ],
      )));
      if (requested == null || !mounted) return;
      await _run(() async { await _api.reserve(widget.institutionId,
          resourceId: resource['id'] as String, purpose: requested['purpose'] as String,
          startsAt: requested['start'] as DateTime, endsAt: requested['end'] as DateTime); });
    } finally { purpose.dispose(); }
  }

  Future<void> _report(Map<String, dynamic> resource) async {
    if (!_canReserve) return;
    final description = TextEditingController();
    try {
      final reason = await showDialog<String>(context: context, builder: (ctx) =>
        AlertDialog(
          title: Text('Signaler : ${resource['name'] ?? 'ressource'}'),
          content: TextField(controller: description, maxLines: 3, maxLength: 500,
            decoration: const InputDecoration(
              labelText: 'Décrivez le dysfonctionnement (8 caractères minimum)')),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(onPressed: () {
              if (description.text.trim().length < 8) return;
              Navigator.pop(ctx, description.text.trim());
            }, child: const Text('Signaler')),
          ],
        ));
      if (reason == null || !mounted) return;
      final institution = widget.institutionId;
      await _run(() async { await _api.reportMaintenance(institution,
          resource['id'] as String, reason); });
    } finally { description.dispose(); }
  }

  Future<void> _transition(Map<String, dynamic> ticket, String action) async {
    if (!_admin) return;
    final note = TextEditingController();
    final label = action == 'start' ? 'Immobiliser la ressource'
      : action == 'resolve' ? 'Terminer la réparation' : 'Rejeter le signalement';
    try {
      final confirmed = await showDialog<String>(context: context, builder: (ctx) =>
        AlertDialog(title: Text(label),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            if (action == 'start') const Text(
              'Attention : les réservations non terminées seront annulées avec motif maintenance.'),
            TextField(controller: note, maxLength: 500, maxLines: 3,
              decoration: InputDecoration(labelText: action == 'start'
                ? 'Note facultative' : 'Justification obligatoire (8 caractères minimum)')),
          ]),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(onPressed: () {
              if (action != 'start' && note.text.trim().length < 8) return;
              Navigator.pop(ctx, note.text.trim());
            }, child: const Text('Confirmer')),
          ]));
      if (confirmed == null || !mounted) return;
      final institution = widget.institutionId;
      await _run(() async { await _api.transitionMaintenance(institution,
        ticket['id'] as String, action, ticket['row_version'] as int, confirmed); });
    } finally { note.dispose(); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Services du Campus'), actions: [
      IconButton(onPressed: _loading || _saving ? null : _reload,
          tooltip: 'Actualiser', icon: const Icon(Icons.refresh)),
    ]),
    floatingActionButton: !_loading && _admin ? FloatingActionButton.extended(
      onPressed: _saving ? null : _register,
      icon: const Icon(Icons.add), label: const Text('Ressource')) : null,
    body: _loading ? const Center(child: CircularProgressIndicator())
      : _error != null ? Center(child: Padding(padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(_error!), TextButton(onPressed: _reload, child: const Text('Réessayer')),
          ])))
      : ListView(padding: const EdgeInsets.all(16), children: [
        Card(child: ListTile(leading: const Icon(Icons.event_available_outlined),
          title: const Text('Événements universitaires'),
          subtitle: const Text('Conférences, inscriptions et places disponibles'),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => context.push('/campus/events/${Uri.encodeComponent(widget.institutionId)}'))),
        const SizedBox(height: 12),
        Text('Mes alertes Campus', style: Theme.of(context).textTheme.titleLarge),
        if (_alerts.isEmpty) const ListTile(title: Text('Aucune alerte en cours.')),
        for (final alert in _alerts) Card(child: ListTile(
          leading: Icon(alert['level'] == 'urgent' ? Icons.error_outline
            : alert['level'] == 'warning' ? Icons.warning_amber_outlined
            : Icons.info_outline),
          title: Text(alert['title'] as String),
          subtitle: Text('${alert['message']}\nÉchéance : ${alert['occurs_at'] ?? ''}'),
          isThreeLine: true,
        )),
        const SizedBox(height: 12),
        Text('Salles, laboratoires et équipements',
          style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        if (_resources.isEmpty) const ListTile(title: Text('Aucune ressource disponible.')),
        for (final resource in _resources) Card(child: ListTile(
          leading: const Icon(Icons.meeting_room_outlined),
          title: Text(resource['name']?.toString() ?? 'Ressource'),
          subtitle: Text('${resource['code'] ?? ''} · ${resource['location'] ?? ''} · Capacité : ${resource['capacity'] ?? '-'} · ${resource['service_state'] == 'maintenance' ? 'En maintenance' : 'Disponible'}'),
          trailing: _canReserve ? Wrap(children: [
            IconButton(tooltip: 'Signaler un défaut', icon: const Icon(Icons.report_problem_outlined),
              onPressed: _saving || resource['service_state'] == 'maintenance' ? null : () => _report(resource)),
            TextButton(onPressed: _saving || resource['service_state'] == 'maintenance'
              ? null : () => _reserve(resource), child: const Text('Réserver')),
          ]) : null,
        )),
        const SizedBox(height: 18),
        Text('Maintenance des ressources', style: Theme.of(context).textTheme.titleLarge),
        if (_maintenance.isEmpty) const ListTile(title: Text('Aucun signalement accessible.')),
        for (final ticket in _maintenance) Card(child: ListTile(
          title: Text(ticket['description']?.toString() ?? 'Signalement'),
          subtitle: Text('${ticket['status'] ?? ''}'
              '${(ticket['resolution']?.toString() ?? '').isNotEmpty ? ' · ${ticket['resolution']}' : ''}'),
          trailing: _admin && !_saving &&
              (ticket['status'] == 'reported' || ticket['status'] == 'in_progress')
            ? PopupMenuButton<String>(onSelected: (action) => _transition(ticket, action),
                itemBuilder: (ctx) => ticket['status'] == 'reported'
                  ? [const PopupMenuItem(value: 'start', child: Text('Immobiliser')),
                     const PopupMenuItem(value: 'dismiss', child: Text('Rejeter'))]
                  : [const PopupMenuItem(value: 'resolve', child: Text('Remettre en service'))])
            : null,
        )),
        const SizedBox(height: 18),
        Text('Réservations accessibles', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 10),
        if (_bookings.isEmpty) const ListTile(title: Text('Aucune réservation.')),
        for (final booking in _bookings) Card(child: ListTile(
          title: Text(booking['purpose']?.toString() ?? 'Réservation'),
          subtitle: Text('${booking['starts_at'] ?? ''} · ${booking['state'] ?? ''}'
              '${booking['cancellation_reason'] == 'resource_maintenance' ? ' · Annulée pour maintenance' : ''}'),
          trailing: booking['state'] == 'confirmed' && _canReserve
            ? IconButton(tooltip: 'Annuler', icon: const Icon(Icons.cancel_outlined),
                onPressed: _saving ? null : () => _run(() async {
                  await _api.cancel(widget.institutionId, booking['id'] as String,
                      booking['row_version'] as int);
                })) : null,
        )),
      ]),
  );
}

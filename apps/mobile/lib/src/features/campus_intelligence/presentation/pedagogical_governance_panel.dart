import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../infrastructure/campus_intelligence_gateway.dart';

/// Phase 14 metadata administration. Always scoped to an authenticated offering;
/// server performs real RBAC + tenant checks on every request, including writes.
class PedagogicalGovernancePanel extends StatefulWidget {
  const PedagogicalGovernancePanel({super.key, required this.gateway,
    required this.institutionId, required this.offeringId});
  final CampusIntelligenceGateway gateway;
  final String institutionId;
  final String offeringId;

  @override
  State<PedagogicalGovernancePanel> createState() => _PedagogicalGovernancePanelState();
}

class _PedagogicalGovernancePanelState extends State<PedagogicalGovernancePanel> {
  final _objectiveId = TextEditingController();
  final _title = TextEditingController();
  final _questionId = TextEditingController();
  final _blueprintId = TextEditingController();
  Map<String, dynamic>? _report;
  String? _selectedObjective, _error, _notice;
  bool _loading = false, _saving = false;
  int _epoch = 0;

  @override
  void initState() { super.initState(); _reload(); }

  @override
  void didUpdateWidget(covariant PedagogicalGovernancePanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.institutionId != widget.institutionId ||
        oldWidget.offeringId != widget.offeringId ||
        oldWidget.gateway != widget.gateway) {
      ++_epoch;
      _saving = false;
      _report = null;
      _selectedObjective = null;
      _objectiveId.clear(); _title.clear(); _questionId.clear(); _blueprintId.clear();
      _reload();
    }
  }

  @override
  void dispose() {
    _epoch++;
    _objectiveId.dispose(); _title.dispose(); _questionId.dispose();
    _blueprintId.dispose();
    super.dispose();
  }

  String _message(Object e) {
    if (e is DioException) {
      if (e.response?.statusCode == 401) return 'Session expirée. Reconnectez-vous.';
      if (e.response?.statusCode == 403) return 'Accès interdit pour ce cours.';
      if (e.response?.statusCode == 400 || e.response?.statusCode == 422) {
        return 'Opération refusée : vérifier les identifiants et les règles pédagogiques.';
      }
      return 'Serveur indisponible : veuillez réessayer.';
    }
    if (e is ArgumentError) return 'Saisie invalide : vérifier les identifiants et la longueur.';
    return 'Opération non effectuée. Vérifiez la connexion.';
  }

  List<Map<String, dynamic>> get _objectives {
    final value = _report?['objectives'];
    if (value is! List) return [];
    return value.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<void> _reload() async {
    final epoch = ++_epoch;
    setState(() { _loading = true; _saving = false;
      _error = null; _notice = null; _report = null; });
    try {
      final report = await widget.gateway.objectiveReport(widget.institutionId, widget.offeringId);
      if (!mounted || epoch != _epoch) return;
      setState(() {
        _report = report;
        _loading = false;
        if (!_objectives.any((e) => e['objective_id'] == _selectedObjective)) {
          _selectedObjective = null;
        }
      });
    } catch (e) {
      if (!mounted || epoch != _epoch) return;
      setState(() { _loading = false; _error = _message(e); });
    }
  }

  Future<void> _mutate(Future<Map<String, dynamic>> Function() operation,
      String confirmation) async {
    if (_saving || _loading) return;
    final epoch = _epoch;
    setState(() { _saving = true; _error = null; _notice = null; });
    try {
      await operation();
      if (!mounted || epoch != _epoch) return;
      // Fetch server state; never treat the local form as evidence of success.
      final report = await widget.gateway.objectiveReport(widget.institutionId, widget.offeringId);
      if (!mounted || epoch != _epoch) return;
      setState(() { _report = report; _notice = confirmation; _saving = false; });
    } catch (e) {
      if (!mounted || epoch != _epoch) return;
      setState(() { _error = _message(e); _saving = false; });
    }
  }

  static String _label(Map<String, dynamic> item) =>
      (item['objective_title'] ?? item['title'] ?? item['objective_id'] ?? 'Objectif').toString();

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(padding: const EdgeInsets.all(14), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Objectifs et traçabilité pédagogique',
          style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 6),
        const Text('Gestion des métadonnées pédagogiques du cours. '
          'Aucune note ou décision du jury n’est modifiée.'),
        if (_loading || _saving) const LinearProgressIndicator(),
        if (_error != null) ...[
          const SizedBox(height: 8),
          Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
        ],
        if (_notice != null) ...[
          const SizedBox(height: 8), Text(_notice!),
        ],
        Align(alignment: Alignment.centerRight, child: TextButton.icon(
          onPressed: _saving || _loading ? null : _reload,
          icon: const Icon(Icons.refresh), label: const Text('Vérifier les objectifs'))),
        if (_report != null) ...[
          Text('${_objectives.length} objectifs déclarés (preuve ≠ note officielle)'),
          for (final item in _objectives)
            ListTile(
              title: Text(_label(item)),
              subtitle: Text('Identifiant : ${item['objective_id'] ?? '—'} · '
                'Intégrité : ${item['evidence_integrity'] ?? 'non certifiée'} · '
                'Origine : ${item['mapping_provenance'] ?? 'non datée'}'),
              // Never render individual scores here, even from unexpected payloads.
            ),
          const Divider(),
          Text('Créer un objectif', style: Theme.of(context).textTheme.titleSmall),
          TextField(controller: _objectiveId, enabled: !_saving,
            maxLength: 120, decoration: const InputDecoration(labelText: 'Code objectif')),
          TextField(controller: _title, enabled: !_saving,
            maxLength: 500, decoration: const InputDecoration(labelText: 'Intitulé de l’objectif')),
          FilledButton.icon(
            onPressed: _saving || _loading ? null : () => _mutate(
              () => widget.gateway.registerObjective(widget.institutionId, widget.offeringId,
                objectiveId: _objectiveId.text, title: _title.text),
              'Objectif enregistré et contrôlé par le serveur.'),
            icon: const Icon(Icons.add), label: const Text('Enregistrer l’objectif')),
          const Divider(),
          Text('Associer une question existante',
            style: Theme.of(context).textTheme.titleSmall),
          const Text('Une association postérieure à l’évaluation ne prouve pas '
            'qu’elle existait lors de la notation.'),
          DropdownButtonFormField<String>(initialValue: _selectedObjective, isExpanded: true,
            decoration: const InputDecoration(labelText: 'Objectif enregistré'),
            items: _objectives.map((row) => DropdownMenuItem<String>(
              value: row['objective_id']?.toString(), child: Text(_label(row),
                overflow: TextOverflow.ellipsis))).toList(),
            onChanged: _saving ? null : (id) => setState(() => _selectedObjective = id)),
          TextField(controller: _questionId, enabled: !_saving,
            decoration: const InputDecoration(labelText: 'Identifiant de la question existante')),
          OutlinedButton.icon(onPressed: _saving || _selectedObjective == null ? null : () =>
            _mutate(() => widget.gateway.mapQuestion(widget.institutionId, widget.offeringId,
              objectiveId: _selectedObjective!, questionId: _questionId.text.trim()),
              'Association enregistrée ; provenance historique conservée.'),
            icon: const Icon(Icons.link), label: const Text('Associer la question')),
          const Divider(),
          Text('Lier une évaluation existante', style: Theme.of(context).textTheme.titleSmall),
          TextField(controller: _blueprintId, enabled: !_saving,
            decoration: const InputDecoration(labelText: 'Identifiant de l’évaluation')),
          OutlinedButton.icon(onPressed: _saving ? null : () => _mutate(
            () => widget.gateway.bindBlueprint(widget.institutionId, widget.offeringId,
              blueprintId: _blueprintId.text.trim()),
            'Évaluation liée au cours et vérifiée par le serveur.'),
            icon: const Icon(Icons.assignment_turned_in_outlined),
            label: const Text('Lier l’évaluation')),
          for (final limitation in _report?['limitations'] is List
              ? _report!['limitations'] as List : const [])
            Padding(padding: const EdgeInsets.only(top: 6),
              child: Text('Limite : $limitation',
                style: Theme.of(context).textTheme.bodySmall)),
        ],
      ])),
  );
}

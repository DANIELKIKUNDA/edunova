import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../infrastructure/campus_intelligence_gateway.dart';
import 'pedagogical_governance_panel.dart';
import 'institutional_archive_panel.dart';

/// A single institution-bound workspace for the canonical Phase 14 and 15 APIs.
/// Authorization and privacy decisions ALWAYS come from the backend.
class InstitutionIntelligencePage extends ConsumerStatefulWidget {
  const InstitutionIntelligencePage({super.key, required this.institutionId});
  final String institutionId;

  @override
  ConsumerState<InstitutionIntelligencePage> createState() => _InstitutionIntelligencePageState();
}

class _InstitutionIntelligencePageState extends ConsumerState<InstitutionIntelligencePage>
    with WidgetsBindingObserver {
  Map<String, dynamic>? _institution, _membership, _teacher, _reconciliation,
      _executive, _comparison;
  List<Map<String, dynamic>> _offerings = [], _periods = [];
  String? _offering, _period, _previous, _current;
  String? _error, _teacherError, _executiveError, _comparisonError;
  bool _loading = true, _teacherLoading = false, _executiveLoading = false,
      _comparisonLoading = false;
  int _revision = 0;
  int _teacherRequest = 0, _executiveRequest = 0, _comparisonRequest = 0;

  CampusIntelligenceGateway get _gateway => ref.read(campusIntelligenceGatewayProvider);
  bool get _active => _membership?['state'] == 'active' && _institution?['state'] == 'active';
  String get _role => (_membership?['role'] ?? '').toString();
  bool get _teacherEnabled => const {
    'owner', 'rector', 'admin', 'academic_admin', 'faculty_admin', 'teacher',
  }.contains(_role);
  bool get _executiveEnabled => const {
    'owner', 'rector', 'admin', 'academic_admin', 'faculty_admin', 'auditor',
  }.contains(_role);
  String? get _unit {
    if (_role != 'faculty_admin') return null;
    return _membership?['unit_id']?.toString();
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _load();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      // Revalidate membership against the server after returning to the app.
      _load();
      return;
    }
    // Screen snapshots/app-switcher must not keep the last aggregate visible.
    ++_revision; ++_teacherRequest; ++_executiveRequest; ++_comparisonRequest;
    if (!mounted) return;
    setState(() {
      _institution = null; _membership = null;
      _teacher = null; _reconciliation = null; _executive = null;
      _comparison = null; _offerings = []; _periods = [];
      _offering = null; _period = null; _previous = null; _current = null;
      _teacherLoading = false; _executiveLoading = false; _comparisonLoading = false;
      _loading = true; _error = null;
    });
  }

  @override
  void didUpdateWidget(covariant InstitutionIntelligencePage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.institutionId != widget.institutionId) {
      // GoRouter may reuse this State when a route changes tenants. Never carry
      // any selection or rendered institutional evidence to the new route.
      _offering = null;
      _period = null;
      _previous = null;
      _current = null;
      _load();
    }
  }

  String _message(Object error) {
    if (error is DioException) {
      switch (error.response?.statusCode) {
        case 401: return 'Session expirée : reconnectez-vous.';
        case 403: return 'Accès refusé pour ce rôle ou ce périmètre.';
        case 404: return 'Ressource introuvable.';
        default: return 'Service indisponible. Vérifiez la connexion et réessayez.';
      }
    }
    if (error is StateError) return 'Authentification requise.';
    if (error is FormatException) return 'Accès institutionnel indisponible ou non autorisé.';
    return 'Données momentanément indisponibles.';
  }

  // A 401/403 is an authorization boundary change, not a cosmetic error.
  // Clear all already-rendered aggregates instead of leaving stale private
  // information on screen after a revoked membership or expired account.
  bool _invalidateOnAccessDenial(Object error) {
    if (error is! DioException ||
        (error.response?.statusCode != 401 && error.response?.statusCode != 403)) {
      return false;
    }
    ++_revision; ++_teacherRequest; ++_executiveRequest; ++_comparisonRequest;
    setState(() {
      _institution = null; _membership = null;
      _teacher = null; _reconciliation = null;
      _executive = null; _comparison = null;
      _offerings = []; _periods = [];
      _offering = null; _period = null; _previous = null; _current = null;
      _teacherLoading = false; _executiveLoading = false;
      _comparisonLoading = false; _loading = false;
      _error = _message(error);
    });
    return true;
  }

  static List<Map<String, dynamic>> _requireUniqueIds(
      List<Map<String, dynamic>> rows) {
    // DropdownButtonFormField asserts if multiple choices have the same value;
    // a malformed API response must fail closed, not crash or silently select
    // an ambiguous academic institution/offering/period reference.
    final seen = <String>{};
    for (final row in rows) {
      final id = row['id'];
      if (id is! String || !RegExp(r'^[a-zA-Z0-9_-]{1,128}$').hasMatch(id)
          || !seen.add(id)) {
        throw const FormatException('Ambiguous or invalid institutional references');
      }
    }
    return rows;
  }

  Future<void> _load() async {
    final revision = ++_revision;
    ++_teacherRequest; ++_executiveRequest; ++_comparisonRequest;
    setState(() {
      _loading = true;
      _error = null;
      _teacher = null;
      _reconciliation = null;
      _executive = null;
      _comparison = null;
      _membership = null;
      _institution = null;
      _offerings = [];
      _periods = [];
      _teacherLoading = false; _executiveLoading = false; _comparisonLoading = false;
      _teacherError = null; _executiveError = null; _comparisonError = null;
    });
    try {
      // Never trust route parameters or saved state to grant access.
      final memberships = await _gateway.institutions();
      final match = memberships.where((row) {
        final institution = row['institution'];
        return institution is Map && institution['id'] == widget.institutionId;
      }).toList();
      if (match.length != 1) throw const FormatException('institution_not_available');
      final selected = match.single;
      final institution = Map<String, dynamic>.from(selected['institution'] as Map);
      final membership = Map<String, dynamic>.from(selected['membership'] as Map);
      if (membership['state'] != 'active' || institution['state'] != 'active') {
        throw const FormatException('membership_not_active');
      }
      final role = membership['role'];
      final canTeach = const {'owner', 'rector', 'admin', 'academic_admin', 'faculty_admin', 'teacher'}.contains(role);
      final canDecide = const {'owner', 'rector', 'admin', 'academic_admin', 'faculty_admin', 'auditor'}.contains(role);
      // The API checks faculty subtrees; do not automatically fall back to all-university data.
      if (role == 'faculty_admin' && (membership['unit_id']?.toString().isNotEmpty != true)) {
        throw const FormatException('faculty_unit_required');
      }
      final offerings = canTeach
          ? _requireUniqueIds(await _gateway.offerings(widget.institutionId))
          : <Map<String, dynamic>>[];
      final periods = canDecide
          ? _requireUniqueIds(await _gateway.periods(widget.institutionId))
          : <Map<String, dynamic>>[];
      if (!mounted || revision != _revision) return;
      setState(() {
        _institution = institution;
        _membership = membership;
        _offerings = offerings;
        _periods = periods; // Historical periods remain selectable for governed archives.
        if (!_offerings.any((x) => x['id'] == _offering)) _offering = _offerings.isEmpty ? null : _offerings.first['id']?.toString();
        if (!_periods.any((x) => x['id'] == _period)) _period = null;
        _previous = null;
        _current = null;
        _loading = false;
      });
      if (canTeach && _offering != null) _loadTeacher();
      if (canDecide) _loadExecutive();
    } catch (e) {
      if (mounted && revision == _revision) {
        setState(() { _error = _message(e); _loading = false; });
      }
    }
  }

  Future<void> _loadTeacher() async {
    final offering = _offering;
    if (!_active || !_teacherEnabled || offering == null) return;
    final revision = _revision, request = ++_teacherRequest;
    setState(() {
      _teacherLoading = true;
      _teacherError = null;
      _teacher = null;
      _reconciliation = null;
    });
    try {
      final dashboard = await _gateway.teachingDashboard(widget.institutionId, offering);
      // Reconciliation is informative and may be unavailable for legacy courses.
      Map<String, dynamic>? reconciliation;
      try {
        reconciliation = await _gateway.gradebookReconciliation(widget.institutionId, offering);
      } catch (error) {
        // A 401/403 revokes the whole workspace, not just the reconciliation.
        if (error is DioException &&
            (error.response?.statusCode == 401 || error.response?.statusCode == 403)) {
          rethrow;
        }
        // Do NOT claim gradebook verification if this optional route fails.
      }
      if (!mounted || revision != _revision || request != _teacherRequest || offering != _offering) return;
      setState(() { _teacher = dashboard; _reconciliation = reconciliation; _teacherLoading = false; });
    } catch (e) {
      if (!mounted || revision != _revision || request != _teacherRequest || offering != _offering) return;
      if (_invalidateOnAccessDenial(e)) return;
      setState(() { _teacherError = _message(e); _teacherLoading = false; });
    }
  }

  Future<void> _loadExecutive() async {
    if (!_active || !_executiveEnabled) return;
    final revision = _revision, period = _period, request = ++_executiveRequest;
    setState(() {
      _executiveLoading = true;
      _executiveError = null;
      _executive = null;
      _comparison = null;
    });
    try {
      final response = await _gateway.executiveReadout(widget.institutionId,
        periodId: period, unitId: _unit);
      if (!mounted || revision != _revision || request != _executiveRequest || period != _period) return;
      setState(() { _executive = response; _executiveLoading = false; });
    } catch (e) {
      if (!mounted || revision != _revision || request != _executiveRequest || period != _period) return;
      if (_invalidateOnAccessDenial(e)) return;
      setState(() { _executiveError = _message(e); _executiveLoading = false; });
    }
  }

  Future<void> _loadComparison() async {
    if (!_active || !_executiveEnabled || _previous == null || _current == null || _previous == _current) return;
    final revision = _revision, previous = _previous!, current = _current!, request = ++_comparisonRequest;
    setState(() { _comparisonLoading = true; _comparisonError = null; _comparison = null; });
    try {
      final data = await _gateway.periodComparison(widget.institutionId,
        previousPeriodId: previous, currentPeriodId: current, unitId: _unit);
      if (!mounted || revision != _revision || request != _comparisonRequest || previous != _previous || current != _current) return;
      setState(() { _comparison = data; _comparisonLoading = false; });
    } catch (e) {
      if (!mounted || revision != _revision || request != _comparisonRequest || previous != _previous || current != _current) return;
      if (_invalidateOnAccessDenial(e)) return;
      setState(() { _comparisonError = _message(e); _comparisonLoading = false; });
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    ++_revision; ++_teacherRequest; ++_executiveRequest; ++_comparisonRequest;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Intelligence Campus'), actions: [
      IconButton(tooltip: 'Actualiser et revérifier les droits', onPressed: _load,
        icon: const Icon(Icons.refresh_rounded)),
    ]),
    body: _loading ? const Center(child: CircularProgressIndicator())
      : _error != null ? _failure(_error!, _load)
      : RefreshIndicator(onRefresh: _load, child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 32), children: [
            Text((_institution?['name'] ?? 'Institution').toString(),
              style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 4),
            Text('Accès institutionnel : $_role · consultation sécurisée en temps réel'),
            const SizedBox(height: 12),
            const _InfoCard('Les analyses sont des aides à la décision humaine. Aucune note officielle ni décision du jury n’est modifiée.'),
            if (!_teacherEnabled && !_executiveEnabled)
              const _InfoCard('Votre rôle ne permet pas d’accéder aux analyses réservées aux enseignants et responsables.'),
            if (_teacherEnabled) ...[
              const SizedBox(height: 24),
              Text('Intelligence pédagogique · Phase 14', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 10),
              if (_offerings.isEmpty) const _InfoCard('Aucun enseignement attribué dans votre espace. Les analyses nécessitent une offre de cours autorisée.'),
              if (_offerings.isNotEmpty)
                DropdownButtonFormField<String>(initialValue: _offering, isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Enseignement autorisé', border: OutlineInputBorder()),
                  items: _offerings.map((x) => DropdownMenuItem<String>(
                    value: x['id']?.toString(),
                    child: Text((x['label'] ?? x['course_id'] ?? 'Cours').toString(), overflow: TextOverflow.ellipsis),
                  )).toList(),
                  onChanged: (value) {
                    setState(() {
                      ++_teacherRequest;
                      _offering = value; _teacher = null; _reconciliation = null;
                      _teacherError = null; _teacherLoading = false;
                    });
                    _loadTeacher();
                  }),
              if (_teacherLoading) const LinearProgressIndicator(),
              if (_teacherError != null) _failure(_teacherError!, _loadTeacher),
              if (_teacher != null) _teacherContent(_teacher!),
            ],
            if (_executiveEnabled) ...[
              const SizedBox(height: 28),
              Text('Intelligence institutionnelle · Phase 15', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(initialValue: _period, isExpanded: true,
                decoration: const InputDecoration(labelText: 'Période du rapport', border: OutlineInputBorder()),
                items: [const DropdownMenuItem<String>(value: null, child: Text('Toutes les périodes autorisées')),
                  ..._periods.map((p) => DropdownMenuItem<String>(value: p['id']?.toString(),
                    child: Text("${p['name'] ?? 'Période'}${p['active'] == false ? ' (historique)' : ''}", overflow: TextOverflow.ellipsis)))],
                onChanged: (value) {
                  setState(() {
                    ++_executiveRequest; ++_comparisonRequest;
                    _period = value; _executive = null; _executiveError = null;
                    _comparison = null; _comparisonError = null; _comparisonLoading = false;
                  });
                  _loadExecutive();
                }),
              if (_role == 'faculty_admin') const _InfoCard('Rapport limité à votre faculté et à ses unités autorisées.'),
              if (_executiveLoading) const LinearProgressIndicator(),
              if (_executiveError != null) _failure(_executiveError!, _loadExecutive),
              if (_executive != null) _executiveContent(_executive!),
              const SizedBox(height: 20),
              _comparisonContent(),
              const SizedBox(height: 20),
              InstitutionalArchivePanel(
                key: ValueKey('archive-${widget.institutionId}-${_unit ?? 'all'}-${_period ?? 'all'}'),
                gateway: _gateway, institutionId: widget.institutionId,
                periodId: _period, unitId: _unit, allowCapture: _role != 'auditor'),
            ],
          ])),
  );

  Widget _teacherContent(Map<String, dynamic> dashboard) {
    final summary = Map<String, dynamic>.from(dashboard['summary'] is Map ? dashboard['summary'] as Map : {});
    final objectives = _items(dashboard['objectives']);
    final actions = _items(dashboard['priority_actions']);
    final errors = _items(dashboard['recurrent_errors']);
    final timeline = _items(dashboard['assessment_timeline']);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const SizedBox(height: 12),
      _InfoCard('Analyse déterministe et descriptive, sans diagnostic individuel ni modèle prédictif.'),
      Wrap(spacing: 8, runSpacing: 8, children: [
        _Chip('${summary['objective_count'] ?? '—'} objectifs'),
        _Chip('${summary['high_priority_count'] ?? '—'} prioritaires'),
        _Chip('${summary['unassessed_count'] ?? '—'} non évalués'),
      ]),
      const SizedBox(height: 12),
      if (objectives.isEmpty) const _InfoCard('Aucune preuve par objectif disponible pour ce cours.'),
      for (final objective in objectives) Card(child: ListTile(
        title: Text((objective['objective_title'] ?? objective['title'] ?? 'Objectif').toString()),
        subtitle: Text('Priorité : ${objective['priority'] ?? 'indéterminée'} · Preuves : ${objective['evidence_integrity'] ?? 'non documentées'}'),
        trailing: Text(objective['aggregate_suppressed'] == true ||
          objective['evidence_integrity'] == 'suppressed'
          ? 'Masqué' : _coverage(objective['coverage'])),
      )),
      if (actions.isNotEmpty) ...[
        const SizedBox(height: 8),
        Text('Pistes d’action pour l’enseignant', style: Theme.of(context).textTheme.titleMedium),
        for (final action in actions) Card(child: ListTile(
          title: Text((action['objective_title'] ?? action['objective_id'] ?? 'Objectif').toString()),
          subtitle: Text((action['reason'] ?? 'Revue pédagogique recommandée').toString()),
        )),
      ],
      if (timeline.isNotEmpty) ...[
        Text('Évolution descriptive des évaluations', style: Theme.of(context).textTheme.titleMedium),
        for (final point in timeline) Card(child: ListTile(
          title: Text((point['objective_title'] ?? 'Objectif').toString()),
          subtitle: Text('Qualité : ${point['evidence_integrity'] ?? 'non établie'} · ${point['mapping_provenance'] ?? 'non documentée'}'),
          trailing: Text(point['evidence_integrity'] == 'suppressed' ||
            (point['assessed_count'] is num && point['assessed_count'] < 3)
            ? 'Masqué' : releasedPercent(point['mean_score'],
                point['mean_score'] == null ? 'suppressed' : 'available')),
        )),
        const _InfoCard('Deux évaluations ne sont pas nécessairement comparables en difficulté ou en barème.'),
      ],
      if (errors.isNotEmpty) ...[
        Text('Erreurs récurrentes (signal collectif)', style: Theme.of(context).textTheme.titleMedium),
        for (final e in errors) Card(child: ListTile(
          title: Text((e['objective_title'] ?? 'Objectif').toString()),
          subtitle: Text('Interprétation descriptive · ${e['evidence_integrity'] ?? 'preuve non certifiée'} · ${e['mapping_provenance'] ?? 'origine inconnue'}'),
        )),
      ],
      const SizedBox(height: 12),
      Text('Rapprochement avec le carnet des notes', style: Theme.of(context).textTheme.titleMedium),
      if (_reconciliation == null) const _InfoCard('Rapprochement non disponible : aucune certification de correspondance des notes.'),
      if (_reconciliation != null) _InfoCard(
        'État : ${_reconciliation!['status'] ?? 'non vérifié'}. '
        'Correspondances candidates : ${_reconciliation!['candidate_count'] ?? 'masquées'}. '
        'La référence est modifiable par le personnel : cela ne certifie pas une note officielle.'),
      if (_offering != null) PedagogicalGovernancePanel(
        key: ValueKey('pedagogy-${widget.institutionId}-$_offering'),
        gateway: _gateway, institutionId: widget.institutionId, offeringId: _offering!),
    ]);
  }

  Widget _executiveContent(Map<String, dynamic> data) {
    final quality = data['quality'] is Map ? Map<String, dynamic>.from(data['quality'] as Map) : <String, dynamic>{};
    final indicators = _items(data['indicators']);
    final priorities = _items(data['priorities']);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const SizedBox(height: 12),
      _InfoCard('Qualité des données : ${quality['status'] ?? 'inconnue'}. '
        'Les valeurs masquées ne doivent jamais être interprétées comme zéro.'),
      for (final indicator in indicators)
        Card(child: ListTile(
          title: Text(_metricLabel((indicator['metric'] ?? '').toString())),
          subtitle: Text('État : ${indicator['status'] ?? 'indisponible'} · Source : ${indicator['source_contract'] ?? 'non vérifiée'}'),
          trailing: SizedBox(width: 114, child: Text(
            releasedPercent(indicator['observed_percent'],
              (indicator['status'] ?? '').toString()),
            maxLines: 2, overflow: TextOverflow.ellipsis, textAlign: TextAlign.end)),
        )),
      if (priorities.isNotEmpty) ...[
        const SizedBox(height: 10),
        Text('Points à examiner (validation humaine)', style: Theme.of(context).textTheme.titleMedium),
        for (final action in priorities) Card(child: ListTile(
          leading: const Icon(Icons.fact_check_outlined),
          title: Text(_metricLabel((action['metric'] ?? '').toString())),
          subtitle: Text((action['recommended_action'] ?? 'Revue humaine requise').toString()),
        )),
      ],
    ]);
  }

  Widget _comparisonContent() => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text('Comparer deux périodes', style: Theme.of(context).textTheme.titleMedium),
    const _InfoCard('Comparaison entre périodes distinctes et actives. Les archives peuvent couvrir des périodes historiques ; le serveur valide chaque comparaison.'),
    for (final previous in [true, false]) Padding(padding: const EdgeInsets.only(top: 8),
      child: DropdownButtonFormField<String>(
        initialValue: previous ? _previous : _current, isExpanded: true,
        decoration: InputDecoration(labelText: previous ? 'Période précédente' : 'Période actuelle',
          border: const OutlineInputBorder()),
        items: _periods.map((p) => DropdownMenuItem<String>(value: p['id']?.toString(),
          child: Text("${p['name'] ?? 'Période'}${p['active'] == false ? ' (historique)' : ''}", overflow: TextOverflow.ellipsis))).toList(),
        onChanged: (v) => setState(() {
          if (previous) { _previous = v; } else { _current = v; }
          ++_comparisonRequest;
          _comparison = null;
          _comparisonError = null;
          _comparisonLoading = false;
        }),
      )),
    const SizedBox(height: 8),
    FilledButton.icon(onPressed: _previous != null && _current != null && _previous != _current && !_comparisonLoading
        ? _loadComparison : null,
      icon: const Icon(Icons.compare_arrows_rounded), label: const Text('Comparer')),
    if (_comparisonLoading) const LinearProgressIndicator(),
    if (_comparisonError != null) _failure(_comparisonError!, _loadComparison),
    if (_comparison != null) ...[
      _InfoCard('Publication : ${(_comparison!['comparison_policy'] as Map?)?['data_release'] ?? 'indisponible'}. Les écarts sont descriptifs, pas causaux.'),
      for (final entry in ((_comparison!['metrics'] as Map?) ?? {}).entries)
        Card(child: ListTile(
          title: Text(_metricLabel(entry.key.toString())),
          subtitle: Text('État : ${(entry.value is Map ? entry.value['status'] : null) ?? 'indisponible'}'),
          trailing: SizedBox(width: 120, child: Text(
            releasedDelta(entry.value is Map &&
                (_comparison!['comparison_policy'] as Map?)?['data_release'] == 'eligible'
                  ? entry.value['delta_percentage_points'] : null,
              entry.value is Map &&
                (_comparison!['comparison_policy'] as Map?)?['data_release'] == 'eligible'
                  ? (entry.value['status'] ?? '').toString() : ''),
            maxLines: 2, overflow: TextOverflow.ellipsis, textAlign: TextAlign.end)),
        )),
    ],
  ]);

  static List<Map<String, dynamic>> _items(dynamic rows) => rows is List
      ? rows.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList(growable: false)
      : <Map<String, dynamic>>[];
  static String _coverage(dynamic value) => value is num && value.isFinite && value >= 0 && value <= 1
      ? '${(value * 100).toStringAsFixed(0)} %' : '—';
  static String _metricLabel(String code) => const {
    'teaching.completion_rate': 'Réalisation des enseignements',
    'teaching.syllabus_coverage_rate': 'Couverture des programmes',
    'attendance.attendance_rate': 'Taux de présence',
    'assignments.submission_rate': 'Remise des travaux',
    'results.pass_rate': 'Réussite académique',
  }[code] ?? code;

  Widget _failure(String message, VoidCallback retry) => Center(child: Padding(
    padding: const EdgeInsets.all(18), child: Column(mainAxisSize: MainAxisSize.min,
      children: [const Icon(Icons.lock_outline_rounded), Text(message),
        TextButton(onPressed: retry, child: const Text('Réessayer'))]),
  ));
}

class _InfoCard extends StatelessWidget {
  const _InfoCard(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(14),
    child: Row(children: [const Icon(Icons.info_outline_rounded), const SizedBox(width: 12),
      Expanded(child: Text(text))])));
}

class _Chip extends StatelessWidget {
  const _Chip(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Chip(label: Text(text));
}

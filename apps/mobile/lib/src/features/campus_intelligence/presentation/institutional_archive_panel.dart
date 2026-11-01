import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../infrastructure/campus_intelligence_gateway.dart';

/// Phase 15 governed archives, comparisons and volatile CSV preview.
/// Never renders withheld snapshot payloads or stores archives on the device.
class InstitutionalArchivePanel extends StatefulWidget {
  const InstitutionalArchivePanel({super.key, required this.gateway,
    required this.institutionId, this.periodId, this.unitId, this.allowCapture = true});
  final CampusIntelligenceGateway gateway;
  final String institutionId;
  final String? periodId, unitId;
  final bool allowCapture;

  @override
  State<InstitutionalArchivePanel> createState() => _InstitutionalArchivePanelState();
}

class _InstitutionalArchivePanelState extends State<InstitutionalArchivePanel>
    with WidgetsBindingObserver {
  List<Map<String, dynamic>>? _history;
  Map<String, dynamic>? _comparison;
  String? _error, _notice, _previewCsv;
  bool _loading = false, _busy = false;
  int _generation = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _reload();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _reload();
      return;
    }
    ++_generation;
    if (!mounted) return;
    setState(() {
      _previewCsv = null; _comparison = null; _history = null;
      _busy = false; _loading = true;
    });
  }
  @override
  void didUpdateWidget(covariant InstitutionalArchivePanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.institutionId != widget.institutionId ||
        oldWidget.periodId != widget.periodId || oldWidget.unitId != widget.unitId ||
        oldWidget.gateway != widget.gateway ||
        oldWidget.allowCapture != widget.allowCapture) {
      // A tenant/period/permission change invalidates even an open confirmation
      // or a pending CSV response. Never reuse the earlier scope's preview.
      ++_generation;
      _busy = false;
      _history = null; _comparison = null; _previewCsv = null;
      _error = null; _notice = null;
      _reload();
    }
  }
  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _generation++;
    super.dispose();
  }

  String _friendly(Object e) {
    if (e is DioException) {
      if (e.response?.statusCode == 401) return 'Session expirée : reconnectez-vous.';
      if (e.response?.statusCode == 403) return 'Accès interdit ou périmètre non autorisé.';
      return 'Données temporairement indisponibles.';
    }
    if (e is FormatException) return 'Réponse non exploitable ou export trop volumineux.';
    return 'Opération impossible. Vérifiez votre connexion.';
  }

  // Drop previously released values after any explicit authorization refusal.
  void _clearOnAccessDenial(Object e) {
    if (e is DioException &&
        (e.response?.statusCode == 401 || e.response?.statusCode == 403)) {
      _history = null;
      _comparison = null;
      _previewCsv = null;
    }
  }

  Future<void> _reload() async {
    final generation = ++_generation;
    setState(() { _loading = true; _history = null; _comparison = null;
      _previewCsv = null; _error = null; _notice = null; });
    try {
      final history = await widget.gateway.snapshotHistory(widget.institutionId,
        periodId: widget.periodId, unitId: widget.unitId);
      if (!mounted || generation != _generation) return;
      setState(() { _history = history; _loading = false; });
    } catch (e) {
      if (!mounted || generation != _generation) return;
      setState(() { _clearOnAccessDenial(e); _error = _friendly(e); _loading = false; });
    }
  }

  Future<void> _capture() async {
    if (_busy || _loading || !widget.allowCapture) return;
    final generation = _generation;
    final confirmed = await showDialog<bool>(context: context,
      builder: (context) => AlertDialog(
        title: const Text('Créer une archive institutionnelle ?'),
        content: const Text('Cette opération crée une capture immuable côté serveur. '
          'Les politiques de confidentialité peuvent interdire sa publication '
          'et les comparaisons ultérieures. Aucune note n’est modifiée.'),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Confirmer la capture')),
        ]));
    if (confirmed != true || !mounted || generation != _generation ||
        !widget.allowCapture) {
      return;
    }
    setState(() { _busy = true; _error = null; _notice = null;
      _previewCsv = null; });
    try {
      await widget.gateway.captureSnapshot(widget.institutionId,
        periodId: widget.periodId, unitId: widget.unitId);
      if (!mounted || generation != _generation) return;
      final history = await widget.gateway.snapshotHistory(widget.institutionId,
        periodId: widget.periodId, unitId: widget.unitId);
      if (!mounted || generation != _generation) return;
      setState(() { _history = history; _comparison = null; _busy = false;
        _notice = 'Capture créée. Affichage soumis aux contrôles du serveur.'; });
    } catch (e) {
      if (!mounted || generation != _generation) return;
      setState(() { _clearOnAccessDenial(e); _error = _friendly(e); _busy = false; });
    }
  }

  Future<void> _compare() async {
    if (_busy || _loading) return;
    final generation = _generation;
    setState(() { _busy = true; _comparison = null; _error = null;
      _previewCsv = null; });
    try {
      final response = await widget.gateway.archiveComparison(widget.institutionId,
        periodId: widget.periodId, unitId: widget.unitId);
      if (!mounted || generation != _generation) return;
      setState(() { _comparison = response; _busy = false; });
    } catch (e) {
      if (!mounted || generation != _generation) return;
      setState(() { _clearOnAccessDenial(e); _error = _friendly(e); _busy = false; });
    }
  }

  Future<void> _csvPreview() async {
    if (_busy || _loading) return;
    final generation = _generation;
    setState(() { _busy = true; _error = null; _previewCsv = null; });
    try {
      // Ephemeral inline preview: unlike a dialog route, it is removed as soon
      // as the institution, unit, period or permission changes.
      final csv = await widget.gateway.csvPreview(widget.institutionId,
        periodId: widget.periodId, unitId: widget.unitId);
      if (!mounted || generation != _generation) return;
      setState(() { _busy = false; _previewCsv = csv; });
    } catch (e) {
      if (!mounted || generation != _generation) return;
      setState(() { _clearOnAccessDenial(e); _error = _friendly(e); _busy = false; });
    }
  }

  @override
  Widget build(BuildContext context) => Card(child: Padding(
    padding: const EdgeInsets.all(14), child: Column(
      crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Archives et exports gouvernés', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 5),
        const Text('Les archives ne sont pas des preuves d’anonymisation. '
          'La comparaison historique peut être volontairement bloquée.'),
        if (_loading || _busy) const LinearProgressIndicator(),
        if (_error != null) Padding(padding: const EdgeInsets.only(top: 8),
          child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
        if (_notice != null) Padding(padding: const EdgeInsets.only(top: 8),
          child: Text(_notice!)),
        Wrap(spacing: 8, runSpacing: 4, children: [
          TextButton.icon(onPressed: _busy || _loading ? null : _reload,
            icon: const Icon(Icons.refresh), label: const Text('Actualiser')),
          if (widget.allowCapture) OutlinedButton.icon(onPressed: _busy || _loading ? null : _capture,
            icon: const Icon(Icons.archive_outlined), label: const Text('Créer une capture')),
          OutlinedButton.icon(onPressed: _busy || _loading ? null : _compare,
            icon: const Icon(Icons.compare), label: const Text('Comparer les archives')),
          OutlinedButton.icon(onPressed: _busy || _loading ? null : _csvPreview,
            icon: const Icon(Icons.table_view_outlined), label: const Text('Aperçu CSV sécurisé')),
        ]),
        if (_previewCsv != null) ...[
          const Divider(),
          Row(children: [
            const Expanded(child: Text('Aperçu CSV gouverné (volatile, non enregistré)')),
            TextButton(onPressed: () => setState(() => _previewCsv = null),
              child: const Text('Fermer l’aperçu')),
          ]),
          Text(_previewCsv!, maxLines: 80, overflow: TextOverflow.ellipsis),
        ],
        if (_history != null) ...[
          Text('Archives accessibles : ${_history!.length}',
            style: Theme.of(context).textTheme.titleSmall),
          if (_history!.isEmpty) const Text('Aucune capture disponible pour ce périmètre.'),
          for (final item in _history!) ListTile(
            leading: Icon(item['privacy_status'] == 'governed_current_archive'
              ? Icons.verified_user_outlined : Icons.lock_outline),
            title: Text('Capture · ${item['privacy_status'] ?? 'non vérifiée'}'),
            subtitle: const Text('Contenu historique masqué sauf autorisation explicite du serveur.'),
          ),
        ],
        if (_comparison != null) ...[
          const Divider(),
          Text(_comparison!['available'] == true
            ? 'Comparaison historique autorisée par le serveur'
            : 'Comparaison historique indisponible : '
              '${_comparison!['reason'] ?? 'confidentialité ou preuves insuffisantes'}'),
          // Deliberately no raw payload dump and no client-side differencing.
          if (_comparison!['available'] == true && _comparison!['deltas'] is Map)
            for (final entry in (_comparison!['deltas'] as Map).entries)
              ListTile(title: Text(entry.key.toString()),
                trailing: Text(entry.value is Map && entry.value['delta'] is num
                    ? '${entry.value['delta']} points' : 'Indisponible')),
        ],
      ])),
  );
}

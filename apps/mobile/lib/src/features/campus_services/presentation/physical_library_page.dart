import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/di/providers.dart';
import '../infrastructure/campus_services_gateway.dart';

/// Bibliothèque physique : catalogue, exemplaires, prêts et restitutions.
/// Le serveur est l'autorité RBAC; aucune donnée ne reste en cache hors ligne.
class PhysicalLibraryPage extends ConsumerStatefulWidget {
  const PhysicalLibraryPage({super.key, required this.institutionId});
  final String institutionId;

  @override
  ConsumerState<PhysicalLibraryPage> createState() => _PhysicalLibraryPageState();
}

class _PhysicalLibraryPageState extends ConsumerState<PhysicalLibraryPage>
    with WidgetsBindingObserver {
  List<Map<String, dynamic>> _books = [], _copies = [], _loans = [];
  String? _role, _error;
  Map<String, dynamic>? _policy;
  bool _loading = true, _saving = false;
  int _revision = 0;
  CampusServicesGateway get _api => ref.read(campusServicesGatewayProvider);

  bool get _admin => const {'owner', 'rector', 'admin', 'academic_admin'}.contains(_role);
  bool get _canBorrow => _role != null && _role != 'auditor';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _reload();
  }

  @override
  void didUpdateWidget(covariant PhysicalLibraryPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.institutionId != widget.institutionId) _reload();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _reload();
    } else {
      ++_revision;
      if (mounted) setState(() => _clear());
    }
  }

  void _clear() {
    _books = [];
    _copies = [];
    _loans = [];
    _role = null;
    _policy = null;
    _loading = true;
  }

  @override
  void dispose() {
    ++_revision;
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  String _message(Object error) {
    if (error is DioException) {
      if (error.response?.statusCode == 401) return 'Session expirée. Reconnectez-vous.';
      if (error.response?.statusCode == 403) return 'Accès révoqué ou non autorisé.';
      if (error.response?.statusCode == 409) {
        final body = error.response?.data;
        if (body is Map && '${body['detail']}'.contains('policy_concurrent')) {
          return 'La politique a été modifiée par un autre responsable. Actualisez avant de réessayer.';
        }
        return 'Prêt indisponible : quota, retard, prolongation maximale ou modification concurrente.';
      }
    }
    return 'Service de bibliothèque indisponible.';
  }

  Future<void> _reload() async {
    final revision = ++_revision;
    if (!mounted) return;
    setState(() { _clear(); _error = null; });
    try {
      final memberships = await _api.institutions();
      if (!mounted || revision != _revision) return;
      final matches = memberships.where((e) {
        final institution = e['institution'];
        return institution is Map && institution['id'] == widget.institutionId;
      }).toList();
      if (matches.length != 1) throw const FormatException('Institution absente');
      final m = matches.single['membership'];
      final i = matches.single['institution'];
      if (m is! Map || i is! Map || m['state'] != 'active' || i['state'] != 'active') {
        throw const FormatException('Adhésion inactive');
      }
      final role = m['role']?.toString();
      final policy = await _api.physicalLibraryPolicy(widget.institutionId);
      if (!mounted || revision != _revision) return;
      final books = await _api.physicalBooks(widget.institutionId);
      if (!mounted || revision != _revision) return;
      final copies = await _api.physicalCopies(widget.institutionId);
      if (!mounted || revision != _revision) return;
      final loans = await _api.physicalLoans(widget.institutionId);
      if (!mounted || revision != _revision) return;
      setState(() { _books = books; _copies = copies; _loans = loans;
        _role = role; _policy = policy; _loading = false; });
    } catch (error) {
      if (!mounted || revision != _revision) return;
      setState(() { _clear(); _loading = false; _error = _message(error); });
    }
  }

  Future<void> _mutate(Future<void> Function() action) async {
    if (_saving) return;
    setState(() => _saving = true);
    try {
      await action();
      if (mounted) await _reload();
    } catch (error) {
      if (!mounted) return;
      if (error is DioException &&
          (error.response?.statusCode == 401 || error.response?.statusCode == 403)) {
        await _reload();
      }
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(_message(error))));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _addBook() async {
    if (!_admin) return;
    final title = TextEditingController(), author = TextEditingController();
    try {
      final result = await showDialog<List<String>>(context: context, builder: (ctx) =>
        AlertDialog(title: const Text('Nouvel ouvrage physique'),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            TextField(controller: title, decoration: const InputDecoration(labelText: 'Titre')),
            TextField(controller: author, decoration: const InputDecoration(labelText: 'Auteur')),
          ]), actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(onPressed: () {
              if (title.text.trim().isEmpty || author.text.trim().isEmpty) return;
              Navigator.pop(ctx, [title.text.trim(), author.text.trim()]);
            }, child: const Text('Créer')),
          ]));
      if (result != null && mounted) await _mutate(() async {
        await _api.addPhysicalBook(widget.institutionId, title: result[0], author: result[1]);
      });
    } finally { title.dispose(); author.dispose(); }
  }

  Future<void> _addCopy(Map<String, dynamic> book) async {
    if (!_admin) return;
    final barcode = TextEditingController();
    try {
      final result = await showDialog<String>(context: context, builder: (ctx) =>
        AlertDialog(title: const Text('Enregistrer un exemplaire'),
          content: TextField(controller: barcode,
            decoration: const InputDecoration(labelText: 'Code-barres unique')),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(onPressed: () {
              if (barcode.text.trim().isEmpty) return;
              Navigator.pop(ctx, barcode.text.trim());
            }, child: const Text('Ajouter')),
          ]));
      if (result != null && mounted) await _mutate(() async {
        await _api.addPhysicalCopy(widget.institutionId,
            bookId: book['id'] as String, barcode: result);
      });
    } finally { barcode.dispose(); }
  }

  Future<void> _editPolicy() async {
    if (!_admin || _policy == null || _saving) return;
    final tenant = widget.institutionId;
    final current = Map<String, dynamic>.from(_policy!);
    final fields = [
      'loan_days', 'max_open_loans', 'max_renewals', 'renewal_days',
    ];
    final labels = [
      'Durée du prêt (1 à 60 jours)', 'Prêts simultanés (1 à 10)',
      'Prolongations (0 à 2)', 'Durée de prolongation (1 à 30 jours)',
    ];
    final limits = [60, 10, 2, 30];
    final minimums = [1, 1, 0, 1];
    final controllers = fields.map((f) =>
        TextEditingController(text: '${current[f] ?? ''}')).toList();
    try {
      final result = await showDialog<List<int>>(context: context, builder: (ctx) =>
        AlertDialog(
          title: const Text('Politique de prêt de l’université'),
          content: SingleChildScrollView(child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ...List.generate(fields.length, (i) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: TextField(controller: controllers[i],
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(labelText: labels[i])),
              )),
              const Text('Les anciennes échéances restent inchangées. '
                  'Les prochaines prolongations suivront les nouvelles règles.'),
            ],
          )),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx),
                child: const Text('Annuler')),
            FilledButton(onPressed: () {
              final values = controllers.map((c) => int.tryParse(c.text.trim())).toList();
              for (var i = 0; i < values.length; i++) {
                if (values[i] == null || values[i]! < minimums[i] || values[i]! > limits[i]) {
                  ScaffoldMessenger.of(ctx).showSnackBar(
                    const SnackBar(content: Text('Valeurs numériques hors limites.')));
                  return;
                }
              }
              Navigator.pop(ctx, values.cast<int>());
            }, child: const Text('Enregistrer')),
          ],
        ));
      // The university can change while a dialog is open. Never apply values
      // selected for the previous tenant to the new tenant.
      if (result != null && mounted && widget.institutionId == tenant && _admin) {
        await _mutate(() async {
          await _api.updatePhysicalLibraryPolicy(tenant,
            expectedVersion: current['row_version'] as int,
            loanDays: result[0], maxOpenLoans: result[1],
            maxRenewals: result[2], renewalDays: result[3]);
        });
      }
    } finally {
      for (final controller in controllers) { controller.dispose(); }
    }
  }

  Future<void> _reportIncident(Map<String, dynamic> loan, String condition) async {
    if (!_admin || _saving || loan['returned_at'] != null) return;
    final tenant = widget.institutionId;
    final revision = _revision;
    final label = condition == 'lost' ? 'perdu' : 'détérioré';
    final confirmed = await showDialog<bool>(context: context, builder: (ctx) =>
      AlertDialog(
        title: Text('Signaler un exemplaire $label'),
        content: const Text('Cette opération clôt le prêt et retire immédiatement '
            'l’exemplaire de la circulation. Confirmez uniquement après '
            'constat par le personnel de la bibliothèque.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Confirmer')),
        ],
      ));
    if (confirmed != true || !mounted || !_admin || _revision != revision ||
        widget.institutionId != tenant) return;
    await _mutate(() async {
      await _api.reportPhysicalLoanIncident(tenant,
          loan['id'] as String, loan['row_version'] as int, condition);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bibliothèque physique'), actions: [
        if (_admin && !_loading) IconButton(tooltip: 'Politique de prêt',
          onPressed: _saving ? null : _editPolicy,
          icon: const Icon(Icons.tune)),
        IconButton(tooltip: 'Actualiser', onPressed: _loading || _saving ? null : _reload,
          icon: const Icon(Icons.refresh)),
      ]),
      floatingActionButton: !_loading && _admin ? FloatingActionButton.extended(
        onPressed: _saving ? null : _addBook,
        icon: const Icon(Icons.library_add), label: const Text('Ouvrage')) : null,
      body: _loading ? const Center(child: CircularProgressIndicator())
        : _error != null ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(_error!), TextButton(onPressed: _reload, child: const Text('Réessayer')),
          ]))
        : ListView(padding: const EdgeInsets.all(16), children: [
            Text('Catalogue des ouvrages', style: Theme.of(context).textTheme.titleLarge),
            if (_books.isEmpty) const ListTile(title: Text('Aucun ouvrage disponible.')),
            for (final book in _books) Card(child: Column(children: [
              ListTile(title: Text(book['title']?.toString() ?? 'Ouvrage'),
                subtitle: Text(book['author']?.toString() ?? ''),
                trailing: _admin ? IconButton(icon: const Icon(Icons.add_box_outlined),
                  tooltip: 'Ajouter un exemplaire',
                  onPressed: _saving ? null : () => _addCopy(book)) : null),
              for (final copy in _copies.where((c) => c['book_id'] == book['id']))
                ListTile(leading: const Icon(Icons.menu_book_outlined),
                  title: Text('Exemplaire ${copy['barcode'] ?? ''}'),
                  subtitle: Text(copy['condition'] == 'lost' ? 'Déclaré perdu — retiré'
                    : copy['condition'] == 'damaged' ? 'Détérioré — en réparation'
                    : copy['active'] != true ? 'Hors service'
                    : copy['available'] == true ? 'Consultable / empruntable' : 'Exemplaire prêté'),
                  trailing: _admin && copy['condition'] == 'damaged'
                    ? TextButton(onPressed: _saving ? null : () => _mutate(() async {
                        await _api.restoreDamagedPhysicalCopy(widget.institutionId,
                            copy['id'] as String, copy['row_version'] as int);
                      }), child: const Text('Remettre en service'))
                    : _canBorrow && copy['available'] == true
                      ? TextButton(onPressed: _saving ? null : () => _mutate(() async {
                          await _api.borrowPhysicalCopy(widget.institutionId, copy['id'] as String);
                        }), child: const Text('Emprunter')) : null),
            ])),
            const SizedBox(height: 16),
            Text('Mes prêts / prêts accessibles', style: Theme.of(context).textTheme.titleLarge),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text('Prêt : ${_policy?['loan_days'] ?? 21} jours · '
                  '${_policy?['max_open_loans'] ?? 3} exemplaires simultanés maximum · '
                  '${_policy?['max_renewals'] ?? 2} prolongations de '
                  '${_policy?['renewal_days'] ?? 14} jours avant échéance. '
                  'Un prêt en retard bloque les nouveaux emprunts et prolongations.'),
            ),
            if (_loans.isEmpty) const ListTile(title: Text('Aucun prêt.')),
            for (final loan in _loans) Card(child: ListTile(
              title: Text('Exemplaire : ${loan['copy_id'] ?? ''}'),
              subtitle: Text('Échéance : ${loan['due_at'] ?? ''} · '
                  '${loan['closure_reason'] == 'lost' ? 'Perdu' : loan['closure_reason'] == 'damaged' ? 'Détérioré' : loan['returned_at'] != null ? 'Restitué' : loan['overdue'] == true ? 'EN RETARD' : 'En cours'} '
                  '· Prolongations : ${loan['renewal_count'] ?? 0}/${_policy?['max_renewals'] ?? 2}'),
              trailing: loan['returned_at'] != null ||
                  (loan['can_renew'] != true && !_admin) ? null :
                PopupMenuButton<String>(
                  tooltip: 'Actions sur le prêt',
                  enabled: !_saving,
                  icon: const Icon(Icons.more_vert),
                  onSelected: (choice) {
                    if (choice == 'lost' || choice == 'damaged') {
                      _reportIncident(loan, choice);
                      return;
                    }
                    _mutate(() async {
                    if (choice == 'renew') {
                      await _api.renewPhysicalLoan(widget.institutionId,
                          loan['id'] as String, loan['row_version'] as int);
                    } else if (choice == 'return') {
                      await _api.returnPhysicalLoan(widget.institutionId,
                          loan['id'] as String, loan['row_version'] as int);
                    }
                    });
                  },
                  itemBuilder: (_) => [
                    if (loan['can_renew'] == true)
                      PopupMenuItem(value: 'renew', child: Text('Prolonger de ${_policy?['renewal_days'] ?? 14} jours')),
                    if (_admin)
                      const PopupMenuItem(value: 'return', child: Text('Enregistrer la restitution')),
                    if (_admin)
                      const PopupMenuItem(value: 'damaged', child: Text('Signaler détérioration')),
                    if (_admin)
                      const PopupMenuItem(value: 'lost', child: Text('Déclarer perdu')),
                  ],
                ),
            )),
          ]),
    );
  }
}

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/di/providers.dart';

/// Volcano Tech central catalogue. Every write is authorised and version checked server-side.
class PlatformCampusOffersPage extends ConsumerStatefulWidget {
  const PlatformCampusOffersPage({super.key});
  @override
  ConsumerState<PlatformCampusOffersPage> createState() => _PlatformCampusOffersPageState();
}

class _PlatformCampusOffersPageState extends ConsumerState<PlatformCampusOffersPage> {
  List<Map<String, dynamic>> offers = [];
  bool busy = false;
  String? error;

  Future<Options> _auth() async {
    final identity = ref.read(identityRepositoryProvider);
    var session = await identity.currentSession();
    if (session == null) throw StateError('Authentification requise');
    if (session.accessExpired) session = await identity.refresh();
    return Options(headers: {'Authorization': 'Bearer ${session.accessToken}'});
  }

  Future<void> _load() async {
    setState(() { busy = true; error = null; });
    try {
      final result = await ref.read(apiClientProvider).dio.get('/v1/commerce/platform/campus-offers', options: await _auth());
      if (!mounted) return;
      setState(() => offers = (result.data as List).map((item) => Map<String, dynamic>.from(item as Map)).toList());
    } on DioException catch (e) {
      if (mounted) setState(() => error = e.response?.statusCode == 403 ? 'Accès réservé à Volcano Tech.' : 'Catalogue indisponible. Réessayez.');
    } catch (_) {
      if (mounted) setState(() => error = 'Impossible de charger les offres.');
    } finally { if (mounted) setState(() => busy = false); }
  }

  @override
  void initState() { super.initState(); Future.microtask(_load); }

  Future<void> _edit([Map<String, dynamic>? existing]) async {
    final code = TextEditingController(text: existing?['code']?.toString() ?? '');
    final label = TextEditingController(text: existing?['label']?.toString() ?? '');
    final price = TextEditingController(text: existing?['price_cdf']?.toString() ?? '');
    final seats = TextEditingController(text: existing?['seats']?.toString() ?? '100');
    final duration = TextEditingController(text: existing?['duration_days']?.toString() ?? '30');
    final grace = TextEditingController(text: existing?['grace_days']?.toString() ?? '0');
    bool active = existing?['active'] == true;
    String? validation;
    final submitted = await showDialog<bool>(context: context, builder: (dialogContext) => StatefulBuilder(
      builder: (dialogContext, refresh) => AlertDialog(
        title: Text(existing == null ? 'Nouvelle offre Campus' : 'Modifier ${existing['code']}'),
        content: SizedBox(width: 450, child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: code, enabled: existing == null, decoration: const InputDecoration(labelText: 'Code unique (A-Z, 0-9, - et _)')),
          TextField(controller: label, decoration: const InputDecoration(labelText: 'Nom commercial')),
          TextField(controller: price, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Prix en FC')),
          TextField(controller: seats, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Places')),
          TextField(controller: duration, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Durée en jours')),
          TextField(controller: grace, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Délai de grâce en jours')),
          SwitchListTile(title: const Text('Offre publiée'), value: active, onChanged: (value) => refresh(() => active = value)),
          if (validation != null) Text(validation!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
        ]))),
        actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Annuler')),
          FilledButton(onPressed: () {
            final p = int.tryParse(price.text), s = int.tryParse(seats.text), d = int.tryParse(duration.text), g = int.tryParse(grace.text);
            if (!RegExp(r'^[A-Za-z0-9_-]{1,64}$').hasMatch(code.text) || label.text.trim().isEmpty || label.text.length > 160 || p == null || p < 0 || s == null || s < 1 || s > 100000 || d == null || d < 1 || d > 3660 || g == null || g < 0 || g > 90) {
              refresh(() => validation = 'Vérifiez le code, le nom, le tarif et les limites numériques.'); return;
            }
            Navigator.pop(dialogContext, true);
          }, child: const Text('Enregistrer'))],
      ),
    ));
    if (submitted == true) {
      setState(() { busy = true; error = null; });
      try {
        await ref.read(apiClientProvider).dio.put('/v1/commerce/platform/campus-offers/${Uri.encodeComponent(code.text)}',
          data: {'label': label.text.trim(), 'price_cdf': int.parse(price.text), 'seats': int.parse(seats.text),
            'duration_days': int.parse(duration.text), 'grace_days': int.parse(grace.text), 'active': active,
            'expected_revision': existing?['revision'] ?? 0}, options: await _auth());
        await _load();
      } on DioException catch (e) {
        if (mounted) setState(() => error = e.response?.statusCode == 409 ? 'Offre modifiée par un autre administrateur : actualisez avant de réessayer.' : 'Enregistrement refusé par le serveur.');
      } catch (_) { if (mounted) setState(() => error = 'Enregistrement impossible.'); }
      finally { if (mounted) setState(() => busy = false); }
    }
    code.dispose(); label.dispose(); price.dispose(); seats.dispose(); duration.dispose(); grace.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Offres Campus · Volcano Tech'), actions: [IconButton(onPressed: busy ? null : _load, icon: const Icon(Icons.refresh))]),
    floatingActionButton: FloatingActionButton.extended(onPressed: busy ? null : () => _edit(), icon: const Icon(Icons.add), label: const Text('Nouvelle offre')),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      const Text('Catalogue institutionnel versionné. Une offre publiée devient visible aux universités ; son paiement reste confirmé exclusivement par le serveur.'),
      if (busy) const LinearProgressIndicator(),
      if (error != null) Card(child: ListTile(title: Text(error!), trailing: TextButton(onPressed: _load, child: const Text('Réessayer')))),
      for (final offer in offers) Card(child: ListTile(
        leading: Icon(offer['active'] == true ? Icons.verified_outlined : Icons.visibility_off_outlined),
        title: Text('${offer['label']} · ${offer['price_cdf']} FC'),
        subtitle: Text('${offer['code']} · ${offer['seats']} places · ${offer['duration_days']} jours · grâce ${offer['grace_days']} j · rév. ${offer['revision']}'),
        trailing: IconButton(tooltip: 'Modifier', icon: const Icon(Icons.edit_outlined), onPressed: busy ? null : () => _edit(offer)),
      )),
      const SizedBox(height: 18), const Center(child: Text('From Volcano Tech')),
    ]),
  );
}

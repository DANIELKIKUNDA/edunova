import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';

class RegisterPage extends ConsumerStatefulWidget {
  const RegisterPage({super.key});
  @override ConsumerState<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends ConsumerState<RegisterPage> {
  final name = TextEditingController(); final emailOrPhone = TextEditingController(); final password = TextEditingController();
  bool loading = false; String? error;
  @override void dispose(){name.dispose();emailOrPhone.dispose();password.dispose();super.dispose();}

  Future<void> submit() async {
    final value = emailOrPhone.text.trim();
    setState(() { loading = true; error = null; });
    try {
      await ref.read(identityRepositoryProvider).register(
        displayName: name.text.trim(),
        password: password.text,
        email: value.contains('@') ? value : null,
        phoneNumber: value.contains('@') ? null : value,
        deviceName: 'EduNova',
      );
      ref.invalidate(authSessionProvider);
      if (mounted) context.pop(true);
    } catch (_) {
      if (mounted) setState(() => error = 'Création impossible. Vérifie les informations ou utilise un autre identifiant.');
    } finally { if (mounted) setState(() => loading = false); }
  }

  @override Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Créer mon compte')),
    body: ListView(padding: const EdgeInsets.all(20), children: [
      Text('Un seul compte, tous tes appareils', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
      const SizedBox(height: 8),
      const Text('Tes documents privés restent locaux par défaut. Le compte sert à Premium, paiements et synchronisation des données autorisées.'),
      const SizedBox(height: 24),
      TextField(controller: name, textCapitalization: TextCapitalization.words, decoration: const InputDecoration(labelText: 'Nom ou pseudonyme')),
      const SizedBox(height: 12),
      TextField(controller: emailOrPhone, decoration: const InputDecoration(labelText: 'Téléphone ou e-mail')),
      const SizedBox(height: 12),
      TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Mot de passe · 8 caractères minimum')),
      if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
      const SizedBox(height: 22),
      FilledButton(onPressed: loading ? null : submit, child: Padding(padding: const EdgeInsets.symmetric(vertical: 13), child: Text(loading ? 'Création…' : 'Créer mon compte'))),
    ]),
  );
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});
  @override ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final login = TextEditingController();
  final password = TextEditingController();
  bool loading = false;
  String? error;

  @override
  void dispose() { login.dispose(); password.dispose(); super.dispose(); }

  Future<void> submit() async {
    setState(() { loading = true; error = null; });
    try {
      await ref.read(identityRepositoryProvider).login(login: login.text.trim(), password: password.text, deviceName: 'EduNova');
      ref.invalidate(authSessionProvider);
      if (mounted) {
        if (context.canPop()) {
          context.pop(true);
        } else {
          context.go('/bootstrap');
        }
      }
    } catch (_) {
      if (mounted) setState(() => error = 'Connexion impossible. Vérifie tes identifiants et la connexion.');
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Se connecter')),
    body: ListView(padding: const EdgeInsets.all(20), children: [
      const SizedBox(height: 18),
      Text('Retrouve ton EduNova', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w900)),
      const SizedBox(height: 8),
      const Text('Ton Premium, tes reçus et ta progression synchronisée restent liés à ton compte.'),
      const SizedBox(height: 28),
      TextField(controller: login, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Téléphone ou e-mail', prefixIcon: Icon(Icons.person_outline_rounded))),
      const SizedBox(height: 14),
      TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Mot de passe', prefixIcon: Icon(Icons.lock_outline_rounded))),
      if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
      const SizedBox(height: 22),
      FilledButton.icon(onPressed: loading ? null : submit, icon: loading ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.login_rounded), label: const Padding(padding: EdgeInsets.symmetric(vertical: 13), child: Text('Se connecter'))),
      const SizedBox(height: 8),
      TextButton(onPressed: () => context.push('/recovery'), child: const Text('Mot de passe oublié ?')),
      TextButton(onPressed: () => context.push('/register'), child: const Text('Créer un compte EduNova')),
    ]),
  );
}

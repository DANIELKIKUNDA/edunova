import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';

class RecoveryPage extends ConsumerStatefulWidget {
  const RecoveryPage({super.key});
  @override
  ConsumerState<RecoveryPage> createState() => _RecoveryPageState();
}

class _RecoveryPageState extends ConsumerState<RecoveryPage> {
  final login = TextEditingController();
  final code = TextEditingController();
  final password = TextEditingController();
  String? challengeId;
  bool busy = false;

  @override
  void dispose() {
    login.dispose(); code.dispose(); password.dispose(); super.dispose();
  }

  Future<void> _request() async {
    setState(() => busy = true);
    try {
      challengeId = await ref.read(identityRepositoryProvider).requestPasswordRecovery(login.text.trim());
      if (mounted) setState(() {});
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _confirm() async {
    final id = challengeId;
    if (id == null) return;
    setState(() => busy = true);
    try {
      await ref.read(identityRepositoryProvider).confirmPasswordRecovery(challengeId: id, code: code.text.trim(), newPassword: password.text);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Mot de passe réinitialisé.')));
      context.go('/login');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Récupérer mon compte')),
    body: ListView(padding: const EdgeInsets.all(18), children: [
      if (challengeId == null) ...[
        const Text('Saisissez votre téléphone ou e-mail. EduNova enverra un code si un canal de récupération est configuré.'),
        const SizedBox(height: 16),
        TextField(controller: login, decoration: const InputDecoration(labelText: 'Téléphone ou e-mail')),
        const SizedBox(height: 12),
        FilledButton(onPressed: busy ? null : _request, child: const Text('Recevoir un code')),
      ] else ...[
        const Text('Un code temporaire a été envoyé au canal associé au compte.'),
        const SizedBox(height: 16),
        TextField(controller: code, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Code à 6 chiffres')),
        const SizedBox(height: 10),
        TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Nouveau mot de passe')),
        const SizedBox(height: 12),
        FilledButton(onPressed: busy ? null : _confirm, child: const Text('Réinitialiser')),
      ]
    ]),
  );
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../domain/auth_session.dart';

final deviceSessionsProvider = FutureProvider<List<DeviceSession>>((ref) async {
  final session = await ref.watch(identityRepositoryProvider).currentSession();
  if (session == null) return const [];
  return ref.watch(identityRepositoryProvider).listSessions();
});

class SecurityPage extends ConsumerStatefulWidget {
  const SecurityPage({super.key});
  @override
  ConsumerState<SecurityPage> createState() => _SecurityPageState();
}

class _SecurityPageState extends ConsumerState<SecurityPage> {
  final currentController = TextEditingController();
  final nextController = TextEditingController();
  bool saving = false;

  @override
  void dispose() {
    currentController.dispose();
    nextController.dispose();
    super.dispose();
  }

  Future<void> _changePassword() async {
    setState(() => saving = true);
    try {
      await ref.read(identityRepositoryProvider).changePassword(
        currentPassword: currentController.text,
        newPassword: nextController.text,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Mot de passe modifié. Reconnectez-vous.')));
      context.go('/login');
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Impossible de modifier le mot de passe : $e')));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final sessions = ref.watch(deviceSessionsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Sécurité')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 120),
        children: [
          Text('Appareils connectés', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          sessions.when(
            data: (items) => Column(children: [
              if (items.isEmpty) const Card(child: ListTile(title: Text('Aucune session distante active.'))),
              for (final s in items)
                Card(
                  child: ListTile(
                    leading: Icon(s.active ? Icons.verified_user_rounded : Icons.phonelink_erase_rounded),
                    title: Text(s.deviceName ?? 'Appareil EduNova'),
                    subtitle: Text(s.active ? 'Session active' : 'Session expirée ou révoquée'),
                    trailing: s.active
                        ? IconButton(
                            tooltip: 'Révoquer cet appareil',
                            icon: const Icon(Icons.logout_rounded),
                            onPressed: () async {
                              await ref.read(identityRepositoryProvider).revokeSession(s.id);
                              ref.invalidate(deviceSessionsProvider);
                            },
                          )
                        : null,
                  ),
                ),
              if (items.any((e) => e.active))
                OutlinedButton.icon(
                  onPressed: () async {
                    await ref.read(identityRepositoryProvider).logoutAll();
                    if (context.mounted) context.go('/login');
                  },
                  icon: const Icon(Icons.devices_off_rounded),
                  label: const Text('Déconnecter tous les appareils'),
                ),
            ]),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Card(child: ListTile(title: const Text('Sessions indisponibles'), subtitle: Text('$e'))),
          ),
          const SizedBox(height: 24),
          Text('Changer le mot de passe', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 10),
          TextField(controller: currentController, obscureText: true, decoration: const InputDecoration(labelText: 'Mot de passe actuel')),
          const SizedBox(height: 10),
          TextField(controller: nextController, obscureText: true, decoration: const InputDecoration(labelText: 'Nouveau mot de passe')),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: saving ? null : _changePassword,
            icon: const Icon(Icons.password_rounded),
            label: Text(saving ? 'Modification…' : 'Modifier le mot de passe'),
          ),
        ],
      ),
    );
  }
}

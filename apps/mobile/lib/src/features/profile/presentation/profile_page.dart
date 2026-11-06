import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scheme = Theme.of(context).colorScheme;
    final session = ref.watch(authSessionProvider).valueOrNull;
    final entitlement = ref.watch(entitlementProvider).valueOrNull;
    final premium = entitlement?.isPremiumOffline(DateTime.now()) ?? false;
    final profile = ref.watch(academicProfileProvider).valueOrNull;
    return Scaffold(
      appBar: AppBar(title: const Text('Moi')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 120),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Row(children: [
                CircleAvatar(radius: 30, backgroundColor: scheme.primaryContainer, child: const Icon(Icons.person_rounded, size: 30)),
                const SizedBox(width: 14),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(session?.displayName ?? 'Étudiant EduNova', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 3),
                  Text(profile == null ? 'Parcours local' : '${profile.faculty} · ${profile.level} · ${profile.semester}'),
                  if (session == null) const Text('Mode local · compte facultatif jusqu’à Premium/synchronisation', style: TextStyle(fontSize: 12)),
                ])),
              ]),
            ),
          ),
          const SizedBox(height: 12),
          Card(child: ListTile(
            leading: Icon(premium ? Icons.workspace_premium_rounded : Icons.auto_awesome_rounded),
            title: Text(premium ? 'Premium actif' : 'EduNova Premium'),
            subtitle: Text(premium ? '${entitlement?.aiCreditsRemaining ?? 0} crédits IA · accès hors ligne vérifié' : 'Environ 1 USD / 30 jours · Mobile Money'),
            trailing: FilledButton.tonal(onPressed: () => context.push('/premium'), child: Text(premium ? 'Gérer' : 'Découvrir')),
          )),
          const SizedBox(height: 12),
          if (session == null)
            Card(child: ListTile(leading: const Icon(Icons.login_rounded), title: const Text('Se connecter ou créer un compte'), subtitle: const Text('Nécessaire pour Premium, reçus et synchronisation.'), trailing: const Icon(Icons.chevron_right_rounded), onTap: () => context.push('/login'))),
          Card(child: ListTile(leading: const Icon(Icons.account_balance_outlined), title: const Text('Mon université · Campus'), subtitle: const Text('Cours et services institutionnels liés à votre université'), trailing: const Icon(Icons.chevron_right_rounded), onTap: session == null ? null : () => context.push('/campus'))),
          Card(child: ListTile(leading: const Icon(Icons.security_outlined), title: const Text('Sécurité et appareils'), subtitle: const Text('Sessions, mot de passe, révocation'), trailing: const Icon(Icons.chevron_right_rounded), onTap: session == null ? null : () => context.push('/security'))),
          Card(child: ListTile(leading: const Icon(Icons.cloud_sync_outlined), title: const Text('Synchronisation cloud'), subtitle: const Text('Progression, calendrier et parcours · documents privés exclus'), trailing: const Icon(Icons.chevron_right_rounded), onTap: session == null ? null : () => context.push('/sync'))),
          Card(child: ListTile(leading: const Icon(Icons.psychology_alt_outlined), title: const Text('Historique Assistant'), subtitle: const Text('Conversations conservées localement sur cet appareil'), trailing: const Icon(Icons.chevron_right_rounded), onTap: () => context.push('/assistant/history'))),
          Card(child: ListTile(leading: const Icon(Icons.download_for_offline_outlined), title: const Text('Contenus hors connexion'), subtitle: const Text('Téléchargements, espace utilisé et cache'), trailing: const Icon(Icons.chevron_right_rounded), onTap: () => context.push('/offline-storage'))),
          Card(child: ListTile(leading: const Icon(Icons.notifications_active_outlined), title: const Text('Rythme & notifications'), subtitle: const Text('Heures calmes, rappels, série de révision'), trailing: const Icon(Icons.chevron_right_rounded), onTap: () => context.push('/engagement'))),
          for (final item in const [
            (Icons.school_outlined, 'Parcours académique'),
            (Icons.settings_outlined, 'Préférences'),
          ])
            Card(child: ListTile(leading: Icon(item.$1), title: Text(item.$2), trailing: const Icon(Icons.chevron_right_rounded))),
        ],
      ),
    );
  }
}

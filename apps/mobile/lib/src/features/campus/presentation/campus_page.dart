import '../../commerce/presentation/campus_paid_checkout_dialog.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';

/// Campus entry point. Institution IDs are obtained from the authenticated API,
/// never from a user-entered arbitrary tenant ID.
final campusMembershipsProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) =>
  ref.watch(campusIntelligenceGatewayProvider).institutions());

/// Private verified alumni discovery, including graduates without current enrollment.
final campusVerifiedAlumniProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) =>
  ref.watch(campusServicesGatewayProvider).alumniMyInstitutions());

class CampusPage extends ConsumerWidget {
  const CampusPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final c = Theme.of(context).colorScheme;
    final institutions = ref.watch(campusMembershipsProvider);
    final verifiedAlumni = ref.watch(campusVerifiedAlumniProvider);
    return Scaffold(appBar: AppBar(title: const Text('Mon université'), actions: [
      IconButton(tooltip: 'Actualiser mes universités',
        onPressed: () => ref.invalidate(campusMembershipsProvider),
        icon: const Icon(Icons.refresh_rounded)),
    ]), body: ListView(padding: const EdgeInsets.all(18), children: [
      Container(padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(gradient: LinearGradient(colors: [c.primaryContainer, c.secondaryContainer]),
          borderRadius: BorderRadius.circular(24)),
        child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(Icons.account_balance_rounded, size: 34), SizedBox(height: 14),
          Text('EduNova Campus', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
          SizedBox(height: 6),
          Text('Votre espace académique institutionnel, connecté à votre université.'),
        ])),
      const SizedBox(height: 18),
      Text('Mes accès institutionnels', style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(height: 10),
      institutions.when(
        loading: () => const Padding(padding: EdgeInsets.all(20), child: Center(child: CircularProgressIndicator())),
        error: (e, _) => Card(child: Padding(padding: const EdgeInsets.all(16),
          child: Column(children: [
            Text(e is DioException && e.response?.statusCode == 401
                ? 'Connectez-vous pour consulter vos universités.'
                : 'Impossible de récupérer vos accès institutionnels.'),
            TextButton(onPressed: () => ref.invalidate(campusMembershipsProvider),
              child: const Text('Réessayer')),
          ]))),
        data: (rows) => rows.isEmpty
          ? const _CampusCard(icon: Icons.mark_email_unread_outlined,
              title: 'Aucune université associée',
              text: 'Une invitation institutionnelle est nécessaire pour accéder aux services Campus.')
          : Column(children: [
              for (final row in rows)
                Builder(builder: (context) {
                  final institution = row['institution'] is Map
                      ? Map<String, dynamic>.from(row['institution'] as Map) : <String, dynamic>{};
                  final membership = row['membership'] is Map
                      ? Map<String, dynamic>.from(row['membership'] as Map) : <String, dynamic>{};
                  final active = membership['state'] == 'active' && institution['state'] == 'active';
                  final role = (membership['role'] ?? '').toString();
                  final canAnalyze = const {'owner', 'rector', 'admin', 'academic_admin',
                    'faculty_admin', 'teacher', 'auditor'}.contains(role);
                  final id = institution['id']?.toString() ?? '';
                  return Card(child: Column(children: [
                    ListTile(
                      leading: const Icon(Icons.domain_rounded),
                      title: Text((institution['name'] ?? 'Université').toString()),
                      subtitle: Text('Rôle : $role · ${membership['state'] ?? 'inconnu'}'),
                    ),
                    if (active && id.isNotEmpty)
                      _CampusLicenseStatus(institutionId: id),
                    if (active && id.isNotEmpty) Padding(
                      padding: const EdgeInsets.only(left: 12, right: 12, bottom: 8),
                      child: Wrap(spacing: 8, children: [
                        OutlinedButton.icon(
                          icon: const Icon(Icons.meeting_room_outlined),
                          label: const Text('Services Campus'),
                          onPressed: () => context.push('/campus/services/${Uri.encodeComponent(id)}'),
                        ),
                        OutlinedButton.icon(
                          icon: const Icon(Icons.local_library_outlined),
                          label: const Text('Bibliothèque physique'),
                          onPressed: () => context.push('/campus/physical-library/${Uri.encodeComponent(id)}'),
                        ),
                        OutlinedButton.icon(
                          icon: const Icon(Icons.groups_outlined),
                          label: const Text('Réseau Alumni'),
                          onPressed: () => context.push('/campus/alumni/${Uri.encodeComponent(id)}'),
                        ),
                        if (const {'owner','rector','admin'}.contains(role))
                          OutlinedButton.icon(
                            icon: const Icon(Icons.payments_outlined),
                            label: const Text('Renouveler Campus'),
                            onPressed: () => showDialog<void>(context:context,
                              builder: (_) => CampusPaidCheckoutDialog(institutionId:id)),
                          ),
                        if (const {'owner','rector','admin','academic_admin'}.contains(role))
                          OutlinedButton.icon(
                            icon: const Icon(Icons.event_seat_outlined),
                            label: const Text('Salles académiques'),
                            onPressed: () => context.push('/campus/academic-rooms/${Uri.encodeComponent(id)}'),
                          ),
                        if (canAnalyze) OutlinedButton.icon(
                          icon: const Icon(Icons.insights_outlined),
                          label: const Text('Intelligence'),
                          onPressed: () => context.push('/campus/intelligence/${Uri.encodeComponent(id)}'),
                        ),
                      ]),
                    ),
                  ]));
                }),
            ]),
      ),
      const SizedBox(height: 18),
      Text('Mes universités Alumni vérifiées', style: Theme.of(context).textTheme.titleLarge),
      verifiedAlumni.when(
        loading: () => const LinearProgressIndicator(),
        error: (e, _) => TextButton(
          onPressed: () => ref.invalidate(campusVerifiedAlumniProvider),
          child: const Text('Actualiser mes accès Alumni')),
        data: (rows) => rows.isEmpty
          ? const ListTile(title: Text('Aucun réseau Alumni vérifié pour ce compte'),
              subtitle: Text('Un responsable universitaire doit d’abord valider votre profil.'))
          : Column(children: [for (final row in rows)
              if (row['institution_id'] is String && row['name'] is String)
                ListTile(leading: const Icon(Icons.school_outlined),
                  title: Text(row['name'] as String),
                  subtitle: const Text('Accès Alumni individuel vérifié'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push(
                    '/campus/alumni/${Uri.encodeComponent(row['institution_id'] as String)}'))])),
      ),
      const SizedBox(height: 18),
      const _CampusCard(icon: Icons.verified_user_outlined,
        title: 'Accès selon votre rôle',
        text: 'Les tableaux enseignants et institutionnels ne sont accessibles qu’aux membres actifs autorisés. Le serveur vérifie aussi le périmètre de votre faculté.'),
      const _CampusCard(icon: Icons.insights_outlined,
        title: 'Intelligence pédagogique',
        text: 'Objectifs, difficultés collectives, preuves d’évaluation et rapprochement informatif avec le gradebook.'),
      const _CampusCard(icon: Icons.query_stats_rounded,
        title: 'Intelligence institutionnelle',
        text: 'Indicateurs gouvernés, confidentialité des petites cohortes, comparaisons entre périodes et priorités de validation humaine.'),
      const _CampusCard(icon: Icons.cloud_off_outlined,
        title: 'Données sensibles en ligne seulement',
        text: 'Ces statistiques ne sont pas copiées dans le stockage hors ligne du téléphone. Les valeurs masquées par le serveur restent masquées.'),
      const SizedBox(height: 12),
      Center(child: Text('From Volcano Tech', style: TextStyle(color: c.onSurfaceVariant,
        fontSize: 12, fontWeight: FontWeight.w600))),
    ]));
  }
}

/// Commercial status is display-only; every Campus service enforces its own RBAC.
/// A failed lookup never becomes an affirmative Campus entitlement.
class _CampusLicenseStatus extends ConsumerWidget {
  const _CampusLicenseStatus({required this.institutionId});
  final String institutionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final access = ref.watch(campusCombinedAccessProvider(institutionId));
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: access.when(
        loading: () => const ListTile(
          dense: true, leading: Icon(Icons.hourglass_top_outlined),
          title: Text('Vérification de la licence Campus…')),
        error: (_, __) => ListTile(
          dense: true, leading: const Icon(Icons.wifi_off_outlined),
          title: const Text('Licence Campus non vérifiée'),
          subtitle: const Text('Une connexion est nécessaire pour vérifier les droits institutionnels.'),
          trailing: IconButton(
            tooltip: 'Réessayer la vérification',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => ref.invalidate(campusCombinedAccessProvider(institutionId)),
          ),
        ),
        data: (rights) => ListTile(
          dense: true,
          leading: Icon(rights.campusAccess ? Icons.verified_outlined : Icons.lock_outline),
          title: Text(rights.campusAccess ? 'Licence Campus active' : 'Licence Campus non active'),
          subtitle: Text(rights.campusAccess
              ? (rights.campusAccessUntil == null
                  ? 'Accès institutionnel vérifié pour cette université.'
                  : 'Accès Campus valable jusqu’au ${rights.campusAccessUntil!.toLocal().day.toString().padLeft(2, '0')}/${rights.campusAccessUntil!.toLocal().month.toString().padLeft(2, '0')}/${rights.campusAccessUntil!.toLocal().year}.')
              : 'Votre accès personnel Gratuit ou Premium reste indépendant.'),
        ),
      ),
    );
  }
}

class _CampusCard extends StatelessWidget {
  const _CampusCard({required this.icon, required this.title, required this.text});
  final IconData icon;
  final String title, text;
  @override
  Widget build(BuildContext context) => Card(child: Padding(
    padding: const EdgeInsets.all(18),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Icon(icon), const SizedBox(width: 14),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        const SizedBox(height: 5), Text(text),
      ])),
    ]),
  ));
}

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/di/providers.dart';
import '../domain/commerce.dart';
import '../domain/combined_access.dart';

class PremiumPage extends ConsumerStatefulWidget {
  const PremiumPage({super.key});
  @override ConsumerState<PremiumPage> createState() => _PremiumPageState();
}

class _PremiumPageState extends ConsumerState<PremiumPage> {
  final phone = TextEditingController();
  bool loading = false;
  String? message;
  String? selectedProvider;
  @override void dispose(){phone.dispose();super.dispose();}

  Future<bool> ensureAuth() async {
    final session = await ref.read(identityRepositoryProvider).currentSession();
    if (session != null) return true;
    if (!mounted) return false;
    final result = await context.push<bool>('/login');
    return result == true;
  }

  Future<void> buy(PremiumPlan plan) async {
    if (!await ensureAuth()) return;
    if (phone.text.trim().isEmpty) { setState(() => message = 'Entre le numéro Mobile Money à débiter.'); return; }
    setState(() { loading = true; message = null; });
    try {
      final gateway = ref.read(commerceRemoteGatewayProvider);
      final local = ref.read(commerceRepositoryProvider);
      final availableProviders = ref.read(paymentProvidersProvider).valueOrNull ?? const <PaymentProviderOption>[];
      if (availableProviders.isEmpty) throw StateError('payment_unavailable');
      final providerCode = selectedProvider ?? availableProviders.first.code;
      var payment = await gateway.createCheckout(planCode: plan.code, phoneNumber: phone.text.trim(), provider: providerCode);
      await local.savePayment(payment);
      if (payment.actionValue != null && (payment.actionType == 'redirect' || payment.actionType == 'ussd')) {
        final uri = Uri.tryParse(payment.actionValue!);
        if (uri != null) await launchUrl(uri, mode: LaunchMode.externalApplication);
      }
      if (mounted) setState(() => message = payment.userMessage ?? 'Paiement initié. Confirme sur ton téléphone.');
      await _pollPayment(payment.id);
    } catch (_) {
      if (mounted) setState(() => message = 'Paiement non démarré. Aucun montant n’a été activé dans EduNova.');
    } finally { if (mounted) setState(() => loading = false); }
  }

  Future<void> _pollPayment(String id) async {
    final gateway = ref.read(commerceRemoteGatewayProvider);
    final local = ref.read(commerceRepositoryProvider);
    for (var i = 0; i < 6; i++) {
      await Future<void>.delayed(const Duration(seconds: 2));
      final payment = await gateway.getPayment(id);
      await local.savePayment(payment);
      if (payment.terminal) {
        if (payment.succeeded) {
          await ref.read(syncEntitlementProvider)();
          ref.invalidate(entitlementProvider);
          ref.invalidate(combinedAccessProvider);
          ref.invalidate(receiptsProvider);
          if (mounted) setState(() => message = 'Premium activé. Merci et bonne étude !');
        } else if (mounted) {
          setState(() => message = 'Paiement terminé avec le statut : ${payment.state}.');
        }
        return;
      }
    }
    if (mounted) setState(() => message = 'Paiement encore en attente. EduNova le vérifiera à la prochaine synchronisation.');
  }

  @override Widget build(BuildContext context) {
    final plans = ref.watch(premiumPlansProvider);
    final combinedAccess = ref.watch(combinedAccessProvider);
    final entitlement = ref.watch(entitlementProvider).valueOrNull;
    final providers = ref.watch(paymentProvidersProvider);
    final receipts = ref.watch(receiptsProvider).valueOrNull ?? const <ReceiptView>[];
    return Scaffold(
      appBar: AppBar(title: const Text('EduNova Premium')),
      body: ListView(padding: const EdgeInsets.fromLTRB(18, 10, 18, 80), children: [
        _HeroPremium(entitlement: entitlement),
        const SizedBox(height: 12),
        combinedAccess.when(
          loading: () => const Card(child: ListTile(
            leading: Icon(Icons.sync), title: Text('Vérification de mes droits…'))),
          error: (_, __) => const Card(child: ListTile(
            leading: Icon(Icons.wifi_off),
            title: Text('Droits en ligne indisponibles'),
            subtitle: Text('Tes contenus personnels restent accessibles. Connecte-toi pour actualiser tes droits.'),
          )),
          data: (access) => _CombinedAccessCard(access: access),
        ),
        const SizedBox(height: 18),
        providers.when(
          loading: () => const LinearProgressIndicator(),
          error: (_, __) => const Card(child: Padding(padding: EdgeInsets.all(14), child: Text('Aucun canal Mobile Money disponible pour le moment.'))),
          data: (items) {
            if (items.isEmpty) return const Card(child: Padding(padding: EdgeInsets.all(14), child: Text('Paiement temporairement indisponible. Tes données restent accessibles.')));
            return DropdownButtonFormField<String>(
              value: selectedProvider ?? items.first.code,
              decoration: const InputDecoration(labelText: 'Canal de paiement', prefixIcon: Icon(Icons.account_balance_wallet_outlined)),
              items: items.map((p) => DropdownMenuItem(value: p.code, child: Text(p.label))).toList(),
              onChanged: loading ? null : (v) => setState(() => selectedProvider = v),
            );
          },
        ),
        const SizedBox(height: 12),
        plans.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (_, __) => const Card(child: Padding(padding: EdgeInsets.all(18), child: Text('Impossible de charger l’offre. Vérifie Internet.'))),
          data: (items) => Column(children: items.map((plan) => _PlanCard(plan: plan, phone: phone, loading: loading, onBuy: () => buy(plan))).toList()),
        ),
        if (message != null) Padding(padding: const EdgeInsets.only(top: 12), child: Card(child: Padding(padding: const EdgeInsets.all(16), child: Text(message!)))),
        const SizedBox(height: 18),
        Text('Mes reçus', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 8),
        if (receipts.isEmpty) const Text('Aucun reçu pour le moment.') else ...receipts.take(6).map((r) => Card(child: ListTile(leading: const Icon(Icons.receipt_long_rounded), title: Text('${r.amountCdf} FC'), subtitle: Text(r.description), trailing: Text('${r.issuedAt.day}/${r.issuedAt.month}')))),
      ]),
    );
  }
}

class _HeroPremium extends StatelessWidget {
  const _HeroPremium({required this.entitlement});
  final EntitlementSnapshot? entitlement;
  @override Widget build(BuildContext context) {
    final premium = entitlement?.isPremiumOffline(DateTime.now()) ?? false;
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(28), gradient: LinearGradient(colors: [scheme.primaryContainer, scheme.secondaryContainer])),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(premium ? Icons.workspace_premium_rounded : Icons.auto_awesome_rounded, size: 34),
        const SizedBox(height: 12),
        Text(premium ? 'Premium actif' : 'Passe au niveau supérieur', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
        const SizedBox(height: 6),
        Text(premium ? '${entitlement!.aiCreditsRemaining} crédits IA disponibles' : 'Résumés complets, audio, quiz, planning intelligent, hors connexion et quota IA.'),
      ]),
    );
  }
}

class _PlanCard extends StatelessWidget {
  const _PlanCard({required this.plan, required this.phone, required this.loading, required this.onBuy});
  final PremiumPlan plan; final TextEditingController phone; final bool loading; final VoidCallback onBuy;
  @override Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Row(children: [Expanded(child: Text('${plan.name} · ${plan.durationDays} jours', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900))), Text('${plan.priceCdf} FC', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900))]),
    const SizedBox(height: 8),
    Text('${plan.includedAiCredits} crédits IA inclus · bibliothèque personnelle locale sans plafond serveur · hors connexion ${plan.offlineEnabled ? 'inclus' : 'non inclus'}'),
    const SizedBox(height: 16),
    TextField(controller: phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Numéro Mobile Money', prefixIcon: Icon(Icons.phone_android_rounded))),
    const SizedBox(height: 12),
    SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: loading ? null : onBuy, icon: const Icon(Icons.lock_rounded), label: Padding(padding: const EdgeInsets.symmetric(vertical: 12), child: Text(loading ? 'Traitement…' : 'Payer avec Mobile Money')))),
    const SizedBox(height: 8),
    const Text('Aucune activation n’est faite avant confirmation serveur du paiement.', style: TextStyle(fontSize: 12)),
  ])));
}


/// This screen checks personal rights only; a Campus membership must be
/// checked with the selected institution id in the Campus experience.
class _CombinedAccessCard extends StatelessWidget {
  const _CombinedAccessCard({required this.access});
  final CombinedAccessView access;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Mes accès EduNova', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        ListTile(
          leading: Icon(access.personalPremium ? Icons.verified : Icons.menu_book),
          title: Text(access.personalPremium ? 'Premium personnel actif' : 'EduNova Gratuit'),
          subtitle: Text(access.personalPremiumUntil == null
              ? 'Ton accès personnel est indépendant de ton université.'
              : 'Valable jusqu’au ${access.personalPremiumUntil!.toLocal().day.toString().padLeft(2, '0')}/${access.personalPremiumUntil!.toLocal().month.toString().padLeft(2, '0')}/${access.personalPremiumUntil!.toLocal().year}. Indépendant de ton université.'),
        ),
        const ListTile(
          leading: Icon(Icons.school_outlined),
          title: Text('EduNova Campus'),
          subtitle: Text('À vérifier dans ton espace Campus : aucune affiliation n’est déduite de ton abonnement personnel.'),
        ),
      ]),
    ),
  );
}

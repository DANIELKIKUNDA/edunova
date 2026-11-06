import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';

import '../../../core/di/providers.dart';
import '../domain/assistant.dart';

class AssistantPage extends ConsumerStatefulWidget {
  const AssistantPage({
    super.key,
    this.courseId,
    this.documentId,
    this.subjectDomain = 'general',
    this.existingConversationId,
  });
  final String? courseId;
  final String? documentId;
  final String subjectDomain;
  final String? existingConversationId;

  @override
  ConsumerState<AssistantPage> createState() => _AssistantPageState();
}

class _AssistantPageState extends ConsumerState<AssistantPage> {
  final input = TextEditingController();
  final uuid = const Uuid();
  late final String conversationId;
  bool busy = false;
  bool personalConsent = false;
  String task = 'explain';
  String explanationDepth = 'standard';

  bool get isPersonal => widget.documentId != null;
  bool get isExisting => widget.existingConversationId != null;

  @override
  void initState() {
    super.initState();
    conversationId = widget.existingConversationId ?? uuid.v4();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (isExisting) return;
      final now = DateTime.now();
      await ref.read(assistantLocalRepositoryProvider).saveConversation(AssistantConversation(
        id: conversationId,
        title: isPersonal ? 'Assistant du document' : (widget.courseId != null ? 'Assistant du cours' : 'Tuteur général'),
        contextType: isPersonal ? 'personal_document' : (widget.courseId != null ? 'shared_course' : 'no_document'),
        contextId: widget.documentId ?? widget.courseId,
        subjectDomain: widget.subjectDomain,
        createdAt: now,
        updatedAt: now,
      ));
    });
  }

  @override
  void dispose() {
    input.dispose();
    super.dispose();
  }

  Future<void> send() async {
    final q = input.text.trim();
    if (q.isEmpty || busy) return;
    if (isPersonal && !personalConsent) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Autorise d’abord l’analyse distante des extraits nécessaires.')));
      return;
    }
    setState(() => busy = true);
    input.clear();
    final previousMessages = await ref.read(assistantLocalRepositoryProvider).recentMessages(conversationId, limit: 6);
    final conversationTurns = previousMessages.map((m) => {'role': m.role, 'text': m.text}).toList(growable: false);
    final now = DateTime.now();
    await ref.read(assistantLocalRepositoryProvider).saveMessage(AssistantMessage(
      id: uuid.v4(), conversationId: conversationId, role: 'user', text: q, createdAt: now,
    ));
    try {
      List<Map<String, Object?>> localContext = const [];
      if (isPersonal) {
        localContext = await ref.read(documentWorkspaceRepositoryProvider).searchRelevantTextChunks(widget.documentId!, q, limit: 8);
      }
      final answer = await ref.read(assistantRemoteGatewayProvider).ask(
        question: q,
        task: task,
        privacyMode: isPersonal ? 'personal_document' : (widget.courseId != null ? 'shared_course' : 'no_document'),
        courseId: widget.courseId,
        subjectDomain: widget.subjectDomain,
        localContext: localContext,
        consentToRemoteAnalysis: personalConsent,
        conversationTurns: conversationTurns,
        explanationDepth: explanationDepth,
      );
      await ref.read(assistantLocalRepositoryProvider).saveMessage(AssistantMessage(
        id: uuid.v4(),
        conversationId: conversationId,
        role: 'assistant',
        text: answer.text,
        createdAt: DateTime.now(),
        citations: answer.citations,
        grounded: answer.grounded,
        confidence: answer.confidence,
        creditsCharged: answer.creditsCharged,
        provider: answer.provider,
        model: answer.model,
        abstained: answer.abstained,
        cacheHit: answer.cacheHit,
        safetyFlags: answer.safetyFlags,
        routeReason: answer.routeReason,
        groundingCoverage: answer.groundingCoverage,
        sourceCount: answer.sourceCount,
        promptVersion: answer.promptVersion,
      ));
      try {
        await ref.read(syncEntitlementProvider)();
      } catch (_) {
        // L'assistant reste utilisable même si la synchronisation d'entitlement échoue momentanément.
      }
    } catch (e) {
      await ref.read(assistantLocalRepositoryProvider).saveMessage(AssistantMessage(
        id: uuid.v4(), conversationId: conversationId, role: 'system', text: _friendlyError(e), createdAt: DateTime.now(),
      ));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  String _friendlyError(Object e) {
    final raw = '$e';
    if (raw.contains('authentication_required')) return 'Connecte-toi pour utiliser l’assistant IA.';
    if (raw.contains('402')) return 'Ton quota IA est épuisé. Les fonctions Premium hors IA restent disponibles.';
    if (raw.contains('ai_daily_budget_exhausted')) return 'Le plafond quotidien IA d’EduNova est atteint. Réessaie plus tard : aucun crédit n’a été consommé.';
    if (raw.contains('personal_document_ai_disabled')) return 'L’analyse distante des documents personnels est désactivée par la politique de confidentialité actuelle.';
    if (raw.contains('503')) return 'Aucun moteur IA n’est disponible pour le moment.';
    if (raw.contains('remote_analysis_consent_required')) return 'Ton autorisation est requise avant d’envoyer des extraits de ce document.';
    return 'Assistant momentanément indisponible. Réessaie plus tard.';
  }

  void _openCitation(AssistantCitation citation) {
    if (isPersonal && citation.documentId == widget.documentId) {
      context.push('/documents/${citation.documentId}?page=${citation.startPage}');
      return;
    }
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(citation.sectionTitle ?? 'Source du cours', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            Text(citation.startPage == citation.endPage ? 'Page ${citation.startPage}' : 'Pages ${citation.startPage}–${citation.endPage}'),
            const SizedBox(height: 12),
            Text(citation.excerpt),
          ]),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(assistantMessagesProvider(conversationId));
    return Scaffold(
      appBar: AppBar(
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('EduNova Tutor'),
          Text(
            isPersonal ? 'Document personnel · extraits temporaires' : (widget.courseId != null ? 'Tuteur académique · cours sourcé' : 'Tuteur académique'),
            style: Theme.of(context).textTheme.labelSmall,
          ),
        ]),
        actions: [
          IconButton(tooltip: 'Historique local', onPressed: () => context.push('/assistant/history'), icon: const Icon(Icons.history_rounded)),
        ],
      ),
      body: Column(children: [
        if (isPersonal)
          Container(
            margin: const EdgeInsets.fromLTRB(14, 8, 14, 4),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Theme.of(context).colorScheme.secondaryContainer, borderRadius: BorderRadius.circular(16)),
            child: SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              value: personalConsent,
              onChanged: (v) => setState(() => personalConsent = v),
              title: const Text('Autoriser l’analyse IA de ce document', style: TextStyle(fontWeight: FontWeight.w800)),
              subtitle: const Text('Seuls les extraits locaux les plus pertinents sont envoyés. Le PDF original n’est ni téléversé ni ajouté au cache partagé.'),
            ),
          ),
        SizedBox(
          height: 50,
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            scrollDirection: Axis.horizontal,
            children: [
              _TaskChip(value: 'explain', label: 'Expliquer', icon: Icons.lightbulb_outline_rounded, selected: task == 'explain', onTap: () => setState(() => task = 'explain')),
              _TaskChip(value: 'simplify', label: 'Simplifier', icon: Icons.compress_rounded, selected: task == 'simplify', onTap: () => setState(() => task = 'simplify')),
              _TaskChip(value: 'compare', label: 'Comparer', icon: Icons.compare_arrows_rounded, selected: task == 'compare', onTap: () => setState(() => task = 'compare')),
              _TaskChip(value: 'quiz_coach', label: 'Mode socratique', icon: Icons.quiz_outlined, selected: task == 'quiz_coach', onTap: () => setState(() => task = 'quiz_coach')),
              _TaskChip(value: 'check_answer', label: 'Vérifier', icon: Icons.fact_check_outlined, selected: task == 'check_answer', onTap: () => setState(() => task = 'check_answer')),
              _TaskChip(value: 'solve_scientific', label: 'Résoudre', icon: Icons.calculate_outlined, selected: task == 'solve_scientific', onTap: () => setState(() => task = 'solve_scientific')),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 0, 14, 6),
          child: Row(children: [
            Text('Profondeur', style: Theme.of(context).textTheme.labelMedium?.copyWith(fontWeight: FontWeight.w800)),
            const SizedBox(width: 8),
            for (final item in const [('concise','Essentiel'), ('standard','Standard'), ('deep','Approfondi')]) ...[
              ChoiceChip(label: Text(item.$2), selected: explanationDepth == item.$1, onSelected: (_) => setState(() => explanationDepth = item.$1)),
              const SizedBox(width: 6),
            ],
          ]),
        ),
        Expanded(
          child: messages.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(child: Text('$e')),
            data: (items) => items.isEmpty
                ? const _EmptyAssistant()
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
                    itemCount: items.length,
                    itemBuilder: (_, i) => _Bubble(message: items[i], onCitation: _openCitation),
                  ),
          ),
        ),
        SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
            child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Expanded(
                child: TextField(
                  controller: input,
                  minLines: 1,
                  maxLines: 5,
                  textInputAction: TextInputAction.newline,
                  decoration: const InputDecoration(hintText: 'Explique, questionne-moi, donne-moi un indice…', prefixIcon: Icon(Icons.auto_awesome_rounded)),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                onPressed: busy ? null : send,
                icon: busy ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.send_rounded),
              ),
            ]),
          ),
        ),
      ]),
    );
  }
}

class _TaskChip extends StatelessWidget {
  const _TaskChip({required this.value, required this.label, required this.icon, required this.selected, required this.onTap});
  final String value;
  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(right: 8),
        child: ChoiceChip(selected: selected, onSelected: (_) => onTap(), avatar: Icon(icon, size: 17), label: Text(label)),
      );
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.message, required this.onCitation});
  final AssistantMessage message;
  final ValueChanged<AssistantCitation> onCitation;
  @override
  Widget build(BuildContext context) {
    final mine = message.role == 'user';
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 680),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: mine ? scheme.primaryContainer : scheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(18)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(message.text),
          if (message.citations.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: message.citations
                  .map((c) => ActionChip(
                        avatar: const Icon(Icons.menu_book_rounded, size: 16),
                        label: Text(c.startPage == c.endPage ? 'p. ${c.startPage}' : 'pp. ${c.startPage}-${c.endPage}'),
                        onPressed: () => onCitation(c),
                      ))
                  .toList(),
            ),
          ],
          if (message.safetyFlags.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(spacing: 6, runSpacing: 6, children: [
              Chip(avatar: const Icon(Icons.shield_outlined, size: 16), label: Text('${message.safetyFlags.length} signal(aux) de sécurité')),
            ]),
          ],
          if (message.role == 'assistant') ...[
            const SizedBox(height: 8),
            Text('${(message.confidence * 100).round()} % confiance · ${(message.groundingCoverage * 100).round()} % ancrage · ${message.sourceCount} source(s) · ${message.creditsCharged} crédit(s)${message.cacheHit ? ' · cache' : ''}', style: Theme.of(context).textTheme.labelSmall),
          ],
        ]),
      ),
    );
  }
}

class _EmptyAssistant extends StatelessWidget {
  const _EmptyAssistant();
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(30),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.psychology_alt_rounded, size: 52),
            const SizedBox(height: 14),
            Text('Ton tuteur contextuel', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            const Text('Demande une explication, une comparaison, une vérification ou une résolution. Avec un cours sélectionné, EduNova répond à partir des sources disponibles.', textAlign: TextAlign.center),
          ]),
        ),
      );
}

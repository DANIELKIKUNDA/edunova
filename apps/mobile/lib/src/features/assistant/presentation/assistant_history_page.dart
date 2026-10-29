import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../domain/assistant.dart';

class AssistantHistoryPage extends ConsumerWidget {
  const AssistantHistoryPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final history = ref.watch(assistantConversationsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Historique Assistant')),
      body: history.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Historique indisponible\n$e', textAlign: TextAlign.center)),
        data: (items) => items.isEmpty
            ? const _EmptyHistory()
            : ListView.separated(
                padding: const EdgeInsets.fromLTRB(14, 10, 14, 32),
                itemCount: items.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (_, i) => _ConversationTile(conversation: items[i]),
              ),
      ),
    );
  }
}

class _ConversationTile extends ConsumerWidget {
  const _ConversationTile({required this.conversation});
  final AssistantConversation conversation;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final icon = switch (conversation.contextType) {
      'personal_document' => Icons.description_rounded,
      'shared_course' => Icons.school_rounded,
      _ => Icons.psychology_alt_rounded,
    };
    return Card(
      child: ListTile(
        leading: CircleAvatar(child: Icon(icon)),
        title: Text(conversation.title, style: const TextStyle(fontWeight: FontWeight.w800)),
        subtitle: Text('${_contextLabel(conversation.contextType)} · ${_date(conversation.updatedAt)}'),
        trailing: PopupMenuButton<String>(
          onSelected: (v) async {
            if (v == 'delete') {
              await ref.read(assistantLocalRepositoryProvider).deleteConversation(conversation.id);
            }
          },
          itemBuilder: (_) => const [PopupMenuItem(value: 'delete', child: Text('Supprimer'))],
        ),
        onTap: () {
          final qp = <String, String>{'conversationId': conversation.id, 'subjectDomain': conversation.subjectDomain};
          if (conversation.contextType == 'personal_document' && conversation.contextId != null) qp['documentId'] = conversation.contextId!;
          if (conversation.contextType == 'shared_course' && conversation.contextId != null) qp['courseId'] = conversation.contextId!;
          context.push(Uri(path: '/assistant', queryParameters: qp).toString());
        },
      ),
    );
  }

  String _contextLabel(String type) => switch (type) {
    'personal_document' => 'Document personnel',
    'shared_course' => 'Cours EduNova',
    _ => 'Tuteur général',
  };

  String _date(DateTime dt) => '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')} · ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
}

class _EmptyHistory extends StatelessWidget {
  const _EmptyHistory();
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.forum_outlined, size: 48),
            const SizedBox(height: 12),
            Text('Aucune conversation', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 6),
            const Text('Tes conversations sont conservées localement sur cet appareil.', textAlign: TextAlign.center),
          ]),
        ),
      );
}

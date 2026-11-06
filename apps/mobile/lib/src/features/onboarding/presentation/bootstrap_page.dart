import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/providers.dart';
import '../../../app/router.dart' show markCleanAnonymousBootstrapVerified;
import '../../identity/infrastructure/secure_session_store.dart';
import '../../identity/infrastructure/legacy_offline_files_stub.dart'
    if (dart.library.io) '../../identity/infrastructure/legacy_offline_files_native.dart' as legacy_files;

class BootstrapPage extends ConsumerWidget {
  const BootstrapPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Authenticate the installation owner before opening any shared SQLite
    // projection, downloaded file or background offline operation.
    final access = ref.watch(_localAccessProvider);
    return access.when(
      loading: () => const _Splash(),
      error: (error, _) => Scaffold(body: Center(child: Text('Accès local indisponible : $error'))),
      data: (allowed) {
        if (!allowed) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (context.mounted) context.go('/login');
          });
          return const _Splash();
        }
        // The router may allow anonymous offline navigation only after this
        // bootstrap has verified that no unowned legacy data exists.
        markCleanAnonymousBootstrapVerified();
        return const _AuthorizedBootstrap();
      },
    );
  }
}

final _localAccessProvider = FutureProvider<bool>((ref) async {
  final store = ref.read(sessionStoreProvider);
  final session = await store.read();
  if (session != null) return true;
  if (store is SecureSessionStore && await store.ownerAccountId() != null) return false;
  // A legacy cache without ownership must never be rendered anonymously.
  final database = ref.read(appDatabaseProvider);
  final tables = await database.customSelect(
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'local_%'",
  ).get();
  for (final table in tables) {
    final name = table.read<String>('name');
    if (!RegExp(r'^local_[a-z0-9_]+$').hasMatch(name)) continue;
    if ((await database.customSelect('SELECT 1 FROM "$name" LIMIT 1').get()).isNotEmpty) return false;
  }
  return !await legacy_files.hasUnownedOfflineFiles();
});

class _AuthorizedBootstrap extends ConsumerWidget {
  const _AuthorizedBootstrap();
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(academicProfileProvider);
    return profile.when(
      data: (value) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          Future.microtask(() async { try { await ref.read(runDownloadQueueProvider).drain(limit: 2); } catch (_) {} });
          Future.microtask(() async { try { final day=await ref.read(engagementRepositoryProvider).recomputeToday(DateTime.now()); try{await ref.read(engagementRemoteGatewayProvider).syncDay(day);}catch(_){} ref.invalidate(localStreakProvider); } catch (_) {} });
          Future.microtask(() async { try { await ref.read(rescheduleLocalNotificationsProvider).run(); } catch (_) {} });
          if (!context.mounted) return;
          context.go(value == null ? '/onboarding' : '/home');
        });
        return const _Splash();
      },
      loading: () => const _Splash(),
      error: (error, _) => Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.error_outline_rounded, size: 52),
                const SizedBox(height: 16),
                const Text('Impossible d’ouvrir les données locales.', style: TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 8),
                Text(error.toString(), textAlign: TextAlign.center),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Splash extends StatelessWidget {
  const _Splash();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image(image: AssetImage('assets/branding/edunova_logo_official.png'), width: 132, height: 132, fit: BoxFit.contain),
            SizedBox(height: 10),
            Text('From Volcano Tech', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            SizedBox(height: 14),
            SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2)),
          ],
        ),
      ),
    );
  }
}

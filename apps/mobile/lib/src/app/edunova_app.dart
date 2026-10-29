import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/di/providers.dart';
import '../core/theme/edunova_theme.dart';
import '../features/engagement/application/local_notification_scheduler.dart';
import 'router.dart';

class EduNovaApp extends ConsumerStatefulWidget {
  const EduNovaApp({super.key});
  @override ConsumerState<EduNovaApp> createState()=>_EduNovaAppState();
}

class _EduNovaAppState extends ConsumerState<EduNovaApp>{
  AppLifecycleListener? _lifecycle;
  StreamSubscription<NotificationTap>? _notificationSub;
  bool _syncing=false;

  @override void initState(){
    super.initState();
    _lifecycle=AppLifecycleListener(onResume:_onResume);
    Future.microtask(_initializeRuntime);
  }

  Future<void> _initializeRuntime() async {
    await Future.wait([_trySync(), _initializeNotificationNavigation(), _initializeRemotePush()]);
  }

  Future<void> _onResume() async {
    await _trySync();
  }

  Future<void> _initializeRemotePush() async {
    try { await ref.read(remotePushRegistrarProvider).initialize(); } catch (_) {
      // Remote push is optional; EduNova remains fully usable offline.
    }
  }

  Future<void> _initializeNotificationNavigation() async {
    try {
      final scheduler=ref.read(localNotificationSchedulerProvider);
      await scheduler.initialize();
      await _notificationSub?.cancel();
      _notificationSub=scheduler.interactions.listen(_openNotificationTap);
      final initial=await scheduler.takeInitialInteraction();
      if(initial!=null) _openNotificationTap(initial);
    } catch (_) {
      // Notification capability is optional and must never block app startup.
    }
  }

  Future<void> _openNotificationTap(NotificationTap tap) async {
    if(!tap.deepLink.startsWith('/')) return;
    if(tap.notificationId!=null){
      try { await ref.read(engagementRepositoryProvider).markNotificationInteracted(tap.notificationId!); } catch (_) {}
    }
    if(!mounted) return;
    edunovaRouter.go(tap.deepLink);
  }

  @override void dispose(){
    _notificationSub?.cancel();
    _lifecycle?.dispose();
    super.dispose();
  }

  Future<void> _trySync() async{
    if(_syncing) return;
    try{
      final session=await ref.read(identityRepositoryProvider).currentSession();
      if(session==null) return;
      final state=await ref.read(cloudSyncLocalRepositoryProvider).ensureState(session.accountId);
      if(state.lastSyncAt!=null && DateTime.now().toUtc().difference(state.lastSyncAt!).inMinutes<5) return;
      _syncing=true;
      await ref.read(runCloudSyncProvider)();
    }catch(_){
      // Offline-first: cloud availability never blocks the application shell.
    }finally{_syncing=false;}
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'EduNova',
      debugShowCheckedModeBanner: false,
      theme: EduNovaTheme.light,
      darkTheme: EduNovaTheme.dark,
      themeMode: ThemeMode.system,
      routerConfig: edunovaRouter,
    );
  }
}

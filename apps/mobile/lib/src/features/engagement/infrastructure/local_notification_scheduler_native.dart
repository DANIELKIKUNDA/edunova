import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import '../application/local_notification_scheduler.dart';
import '../domain/engagement.dart';

class NativeLocalNotificationScheduler implements LocalNotificationScheduler {
  @override bool get supportsSystemNotifications => Platform.isAndroid || Platform.isIOS;
  final FlutterLocalNotificationsPlugin _plugin=FlutterLocalNotificationsPlugin();
  final StreamController<NotificationTap> _interactions=StreamController<NotificationTap>.broadcast();
  bool _ready=false;
  NotificationTap? _initialInteraction;

  int _id(String value)=>value.codeUnits.fold<int>(17,(a,b)=>((a*31)+b)&0x7fffffff);

  @override Stream<NotificationTap> get interactions => _interactions.stream;

  NotificationTap? _decode(String? payload){
    if(payload==null||payload.trim().isEmpty)return null;
    try{
      final raw=jsonDecode(payload);
      if(raw is Map){
        final link=(raw['link']??'').toString();
        final id=raw['id']?.toString();
        if(link.startsWith('/')) return NotificationTap(deepLink:link,notificationId:id?.isEmpty==true?null:id);
      }
    }catch(_){
      if(payload.startsWith('/')) return NotificationTap(deepLink:payload);
    }
    return null;
  }

  @override Future<void> initialize() async {
    if(_ready)return;
    tzdata.initializeTimeZones();
    if(!Platform.isAndroid && !Platform.isIOS){_ready=true;return;}
    const settings=InitializationSettings(android:AndroidInitializationSettings('@mipmap/ic_launcher'),iOS:DarwinInitializationSettings());
    final launch=await _plugin.getNotificationAppLaunchDetails();
    _initialInteraction=_decode(launch?.notificationResponse?.payload);
    await _plugin.initialize(
      settings: settings,
      onDidReceiveNotificationResponse:(response){
        final tap=_decode(response.payload);
        if(tap!=null)_interactions.add(tap);
      },
    );
    _ready=true;
  }

  @override Future<NotificationTap?> takeInitialInteraction() async {
    await initialize();
    final value=_initialInteraction;
    _initialInteraction=null;
    return value;
  }

  @override Future<bool> requestPermission() async {
    await initialize();
    if(!Platform.isAndroid && !Platform.isIOS)return true;
    final android=await _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()?.requestNotificationsPermission();
    final ios=await _plugin.resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>()?.requestPermissions(alert:true,badge:true,sound:true);
    return android ?? ios ?? true;
  }

  @override Future<void> schedule(LocalNotificationView n) async {
    await initialize();
    if(!Platform.isAndroid && !Platform.isIOS)return;
    const details=NotificationDetails(
      android:AndroidNotificationDetails('edunova_study','Études et échéances',channelDescription:'Rappels pédagogiques EduNova',importance:Importance.high,priority:Priority.high),
      iOS:DarwinNotificationDetails(),
    );
    final payload=jsonEncode({'id':n.id,'link':n.deepLink});
    await _plugin.zonedSchedule(id:_id(n.id),title:n.title,body:n.body,scheduledDate:tz.TZDateTime.from(n.fireAt.toUtc(),tz.UTC),notificationDetails:details,androidScheduleMode:AndroidScheduleMode.inexactAllowWhileIdle,payload:payload);
  }

  @override Future<void> cancel(String id) async {await initialize(); await _plugin.cancel(id:_id(id));}
  @override Future<void> cancelAll() async {await initialize(); await _plugin.cancelAll();}
}
LocalNotificationScheduler createLocalNotificationScheduler()=>NativeLocalNotificationScheduler();

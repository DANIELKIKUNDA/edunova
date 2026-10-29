import 'dart:async';
import 'dart:io';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'api_engagement_gateway.dart';

/// Registers the installation with EduNova's push registry. Firebase credentials
/// remain platform deployment files (google-services.json / GoogleService-Info.plist)
/// and are never committed as application secrets.
class RemotePushRegistrar {
  RemotePushRegistrar(this.gateway);
  final ApiEngagementGateway gateway;
  StreamSubscription<String>? _refresh;
  String? _deviceId;

  Future<void> initialize() async {
    if (!(Platform.isAndroid || Platform.isIOS)) return;
    try {
      if (Firebase.apps.isEmpty) await Firebase.initializeApp();
      final messaging=FirebaseMessaging.instance;
      final permission=await messaging.requestPermission(alert:true,badge:true,sound:true,provisional:false);
      if (permission.authorizationStatus==AuthorizationStatus.denied) return;
      _deviceId=await _installationId();
      final token=await messaging.getToken();
      if (token!=null && token.length>=16) await gateway.registerPushDevice(deviceId:_deviceId!,platform:Platform.isAndroid?'android':'ios',token:token);
      _refresh=messaging.onTokenRefresh.listen((token) async {
        if (token.length>=16 && _deviceId!=null) {
          try { await gateway.registerPushDevice(deviceId:_deviceId!,platform:Platform.isAndroid?'android':'ios',token:token); } catch (_) {}
        }
      });
    } catch (_) {
      // Remote push is best-effort: local/offline notifications remain available.
    }
  }

  Future<String> _installationId() async {
    final info=DeviceInfoPlugin();
    if (Platform.isAndroid) {
      final d=await info.androidInfo;
      return 'android-${d.id}';
    }
    final d=await info.iosInfo;
    return 'ios-${d.identifierForVendor ?? 'unknown'}';
  }

  Future<void> dispose() async { await _refresh?.cancel(); }
}

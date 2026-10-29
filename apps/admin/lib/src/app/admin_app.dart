import 'package:flutter/material.dart';
import '../features/editorial/editorial_api.dart';
import '../features/editorial/editorial_shell.dart';
import '../features/editorial/login_page.dart';
import '../features/platform/platform_shell.dart';

enum _Workspace{platform,studio,none}
class EduNovaAdminApp extends StatefulWidget { const EduNovaAdminApp({super.key}); @override State<EduNovaAdminApp> createState()=>_EduNovaAdminAppState(); }
class _EduNovaAdminAppState extends State<EduNovaAdminApp>{final api=EditorialApi.fromEnvironment();bool booting=true,authenticated=false;_Workspace workspace=_Workspace.none;
 @override void initState(){super.initState();_restore();}
 Future<_Workspace> _resolveWorkspace()async{try{await api.platformMe();return _Workspace.platform;}catch(_){}try{await api.me();return _Workspace.studio;}catch(_){}return _Workspace.none;}
 Future<void> _restore()async{final ok=await api.restore();final w=ok?await _resolveWorkspace():_Workspace.none;if(ok&&w==_Workspace.none)await api.clearSession();if(mounted)setState((){authenticated=ok&&w!=_Workspace.none;workspace=w;booting=false;});}
 Future<void> _authenticated()async{setState(()=>booting=true);final w=await _resolveWorkspace();if(w==_Workspace.none){await api.clearSession();if(mounted)setState((){authenticated=false;workspace=w;booting=false;});return;}if(mounted)setState((){authenticated=true;workspace=w;booting=false;});}
 Future<void> _logout()async{await api.logout();if(mounted)setState((){authenticated=false;workspace=_Workspace.none;});}
 @override Widget build(BuildContext context)=>MaterialApp(debugShowCheckedModeBanner:false,title:'EduNova Administration',theme:ThemeData(useMaterial3:true,colorSchemeSeed:const Color(0xFF275DAD),brightness:Brightness.light,inputDecorationTheme:const InputDecorationTheme(border:OutlineInputBorder(),filled:true),cardTheme:const CardThemeData(elevation:0,margin:EdgeInsets.zero)),darkTheme:ThemeData(useMaterial3:true,colorSchemeSeed:const Color(0xFF6EA8FE),brightness:Brightness.dark,inputDecorationTheme:const InputDecorationTheme(border:OutlineInputBorder(),filled:true),cardTheme:const CardThemeData(elevation:0,margin:EdgeInsets.zero)),home:booting?const _BootScreen():authenticated?(workspace==_Workspace.platform?PlatformShell(api:api,onLogout:_logout):EditorialShell(api:api,onLogout:_logout)):AdminLoginPage(api:api,onAuthenticated:_authenticated));
}
class _BootScreen extends StatelessWidget{const _BootScreen();@override Widget build(BuildContext c)=>Scaffold(body:Center(child:Column(mainAxisSize:MainAxisSize.min,children:[Image.asset('assets/branding/edunova_logo_official.png',height:92),const SizedBox(height:18),const CircularProgressIndicator(),const SizedBox(height:12),const Text('Ouverture d’EduNova…'),const SizedBox(height:4),Text('From Volcano Tech',style:Theme.of(c).textTheme.bodySmall)])));}

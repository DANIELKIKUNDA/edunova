import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class StudioSession {
  final String accountId;
  final String displayName;
  final String accessToken;
  final String refreshToken;
  final int expiresInSeconds;
  const StudioSession({required this.accountId,required this.displayName,required this.accessToken,required this.refreshToken,required this.expiresInSeconds});

  factory StudioSession.fromJson(Map<String,dynamic> json)=>StudioSession(
    accountId:json['account_id'] as String,
    displayName:(json['display_name']??'') as String,
    accessToken:json['access_token'] as String,
    refreshToken:json['refresh_token'] as String,
    expiresInSeconds:(json['expires_in_seconds']??0) as int,
  );
}

class StudioSessionStore {
  static const _storage=FlutterSecureStorage();
  static const _access='studio_access_token',_refresh='studio_refresh_token',_account='studio_account_id',_name='studio_display_name';
  Future<void> save(StudioSession s) async {await Future.wait([_storage.write(key:_access,value:s.accessToken),_storage.write(key:_refresh,value:s.refreshToken),_storage.write(key:_account,value:s.accountId),_storage.write(key:_name,value:s.displayName)]);}
  Future<StudioSession?> read() async {
    final values=await Future.wait([_storage.read(key:_access),_storage.read(key:_refresh),_storage.read(key:_account),_storage.read(key:_name)]);
    if(values[0]==null||values[1]==null||values[2]==null)return null;
    return StudioSession(accountId:values[2]!,displayName:values[3]??'',accessToken:values[0]!,refreshToken:values[1]!,expiresInSeconds:0);
  }
  Future<void> clear()=>_storage.deleteAll();
}

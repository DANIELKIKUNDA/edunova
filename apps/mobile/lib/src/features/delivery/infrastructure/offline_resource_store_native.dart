import 'dart:io';
import 'package:crypto/crypto.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../../../core/database/app_database.dart';
import '../../../core/security/local_account_access.dart';
import '../application/delivery_repository.dart';

class NativeOfflineResourceStore implements OfflineResourceStore {
  final LocalAccountAccess _access = LocalAccountAccess();
  // Resource identifiers are untrusted server data. Never allow a path
  // separator or traversal segment to escape the application cache directory.
  Future<Directory> _dir(String id) async {
    await _access.assertOwned();
    if (id.isEmpty || !RegExp(r'^[A-Za-z0-9_-]+$').hasMatch(id)) {
      throw ArgumentError.value(id, 'id', 'invalid_offline_resource_id');
    }
    final root = await getApplicationSupportDirectory();
    final d = Directory(p.join(root.path, 'offline_library', id));
    await d.create(recursive: true);
    return d;
  }
  Future<File> _partial(String id) async=>File(p.join((await _dir(id)).path,'content.part'));
  Future<File> _final(String id) async=>File(p.join((await _dir(id)).path,'content.bin'));
  @override Future<int> partialLength(String id) async{final f=await _partial(id);return await f.exists()?f.length():0;}
  @override Future<void> resetPartial(String id) async{final f=await _partial(id);if(await f.exists())await f.delete();}
  @override Future<void> append(String id,List<int> bytes) async{final f=await _partial(id);await f.writeAsBytes(bytes,mode:FileMode.append,flush:false);}
  @override Future<String> finalize(String id) async{final part=await _partial(id);final out=await _final(id);if(await out.exists())await out.delete();await part.rename(out.path);return out.path;}
  @override Future<String> sha256Hex(String id,{required bool finalized}) async{final f=finalized?await _final(id):await _partial(id);final digest=await sha256.bind(f.openRead()).first;return digest.toString();}
  @override Future<void> delete(String id) async{final d=await _dir(id);if(await d.exists())await d.delete(recursive:true);}
  @override Future<String?> finalUri(String id) async{final f=await _final(id);return await f.exists()?f.path:null;}
}
OfflineResourceStore createOfflineResourceStore(AppDatabase db)=>NativeOfflineResourceStore();

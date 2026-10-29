import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:drift/drift.dart';
import '../../../core/database/app_database.dart';
import '../../../core/security/local_account_access.dart';
import '../application/delivery_repository.dart';

/// PWA store: binary resources are persisted in fixed chunks inside Drift's web SQLite.
/// Drift Web is OPFS-backed when the platform supports it, so downloads survive reloads
/// without uploading the resource to EduNova servers.
class WebChunkOfflineResourceStore implements OfflineResourceStore {
  WebChunkOfflineResourceStore(this.db); final AppDatabase db;
  final LocalAccountAccess _access = LocalAccountAccess();
  Future<T> _read<T>(Future<T> Function() action) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    final result = await action();
    await _access.assertUnchanged(revision, owned: true);
    return result;
  }
  Future<T> _write<T>(Future<T> Function() action) async {
    final revision = _access.captureRevision();
    await _access.assertUnchanged(revision, owned: true);
    return db.transaction(() async {
      final result = await action();
      await _access.assertUnchanged(revision, owned: true);
      return result;
    });
  }
  @override Future<int> partialLength(String id) async {
    return _read(() async {final rows=await (db.select(db.localLibraryResourceChunks)..where((t)=>t.resourceId.equals(id))).get();return rows.fold<int>(0,(a,b)=>a+b.bytes.length);
    });
  }
  @override Future<void> resetPartial(String id) async {
    await _write(() async => (db.delete(db.localLibraryResourceChunks)..where((t)=>t.resourceId.equals(id))).go());
  }
  @override Future<void> append(String id,List<int> bytes) async {
    await _write(() async {
    final rows=await (db.select(db.localLibraryResourceChunks)..where((t)=>t.resourceId.equals(id))..orderBy([(t)=>OrderingTerm.desc(t.chunkIndex)])..limit(1)).get();
    final idx=rows.isEmpty?0:rows.first.chunkIndex+1; final offset=rows.isEmpty?0:rows.first.byteOffset+rows.first.bytes.length;
    await db.into(db.localLibraryResourceChunks).insert(LocalLibraryResourceChunksCompanion.insert(resourceId:id,chunkIndex:idx,bytes:Uint8List.fromList(bytes),byteOffset:offset,updatedAt:DateTime.now().toUtc()));
  
    });
  }
  @override Future<String> finalize(String id) => _read(() async => 'drift-chunks://$id');
  @override Future<String> sha256Hex(String id,{required bool finalized}) async {
    return _read(() async {
    final rows=await (db.select(db.localLibraryResourceChunks)..where((t)=>t.resourceId.equals(id))..orderBy([(t)=>OrderingTerm.asc(t.chunkIndex)])).get();
    final sink=_DigestSink(); final input=sha256.startChunkedConversion(sink);
    for(final r in rows){input.add(r.bytes);} input.close();
    return sink.value?.toString() ?? sha256.convert(const <int>[]).toString();
  
    });
  }
  @override Future<void> delete(String id) async {
    await resetPartial(id);
  }
  @override Future<String?> finalUri(String id) => _read(() async => await partialLength(id)>0?'drift-chunks://$id':null);
}
class _DigestSink implements Sink<Digest> {
  Digest? value;
  @override void add(Digest data){value=data;}
  @override void close(){}
}

OfflineResourceStore createOfflineResourceStore(AppDatabase db)=>WebChunkOfflineResourceStore(db);

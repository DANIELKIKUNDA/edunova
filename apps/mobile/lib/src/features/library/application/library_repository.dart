import '../domain/library.dart';

abstract interface class LibraryLocalRepository {
  Stream<List<LibraryCourseView>> watchCourses();
  Future<String?> catalogEtag(String cacheKey);
  Future<void> replaceCatalogScope(List<LibraryCourseView> courses,{required String cacheKey,String? facultyDomain,String? program,String? level,String? semester,required String etag});
  Future<void> saveManifest(LibraryManifest manifest);
  Stream<List<LibraryResourceView>> watchResources(String versionId);
  Future<void> setCourseFollowed(String courseId, bool followed);
}

abstract interface class LibraryRemoteGateway {
  Future<LibraryCatalogPage> loadCatalogPage({String? facultyDomain,String? program,String? level,String? semester,String? cursor,String? ifNoneMatch,int limit=200});
  Future<LibraryManifest> loadManifest(String courseId);
}

class RefreshLibraryCatalog {
  const RefreshLibraryCatalog(this.local,this.remote);
  final LibraryLocalRepository local;
  final LibraryRemoteGateway remote;

  String _cacheKey(String? faculty,String? program,String? level,String? semester)=>[faculty??'',program??'',level??'',semester??''].join('|');

  Future<int> call({String? facultyDomain,String? program,String? level,String? semester}) async {
    final key=_cacheKey(facultyDomain,program,level,semester);
    final knownEtag=await local.catalogEtag(key);
    final first=await remote.loadCatalogPage(
      facultyDomain:facultyDomain,program:program,level:level,semester:semester,ifNoneMatch:knownEtag,limit:200,
    );
    if(first.notModified) return 0;
    final all=<LibraryCourseView>[...first.courses];
    var cursor=first.nextCursor;
    var pages=1;
    while(cursor!=null && pages<20){
      final page=await remote.loadCatalogPage(
        facultyDomain:facultyDomain,program:program,level:level,semester:semester,cursor:cursor,limit:200,
      );
      // Offset pagination is safe only while the filtered catalog fingerprint stays stable.
      // If a publication happens during refresh, keep the old local cache and retry later.
      if(page.etag!=first.etag){
        throw StateError('catalog_changed_during_refresh');
      }
      all.addAll(page.courses);
      cursor=page.nextCursor;
      pages++;
    }
    if(cursor!=null){
      throw StateError('catalog_page_limit_exceeded');
    }
    await local.replaceCatalogScope(
      all,cacheKey:key,facultyDomain:facultyDomain,program:program,level:level,semester:semester,etag:first.etag,
    );
    return all.length;
  }
}

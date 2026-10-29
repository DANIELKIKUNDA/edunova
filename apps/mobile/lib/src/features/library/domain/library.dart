class LibraryCourseView {
  const LibraryCourseView({required this.id,required this.facultyDomain,required this.program,required this.level,required this.semester,required this.title,required this.slug,required this.description,required this.premiumRequired,this.activeVersionId,required this.updatedAt,this.followed=false});
  final String id,facultyDomain,program,level,semester,title,slug,description;
  final bool premiumRequired;
  final String? activeVersionId;
  final DateTime updatedAt;
  final bool followed;
}

class LibraryVersionView {
  const LibraryVersionView({required this.id,required this.courseId,required this.label,this.academicYear,required this.sourceFingerprint,required this.changelog,this.publishedAt});
  final String id,courseId,label,sourceFingerprint,changelog;
  final String? academicYear;
  final DateTime? publishedAt;
}

class LibraryResourceView {
  const LibraryResourceView({required this.id,required this.versionId,required this.kind,required this.title,this.mimeType,this.sizeBytes,this.checksumSha256,required this.premiumRequired,required this.offlineAllowed,required this.access,this.deliveryToken});
  final String id,versionId,kind,title,access;
  final String? mimeType,checksumSha256,deliveryToken;
  final int? sizeBytes;
  final bool premiumRequired,offlineAllowed;
}

class LibraryManifest {
  const LibraryManifest({required this.course,required this.version,required this.resources,required this.premium});
  final LibraryCourseView course;
  final LibraryVersionView version;
  final List<LibraryResourceView> resources;
  final bool premium;
}

class LibraryCatalogPage {
  const LibraryCatalogPage({required this.courses,required this.etag,this.nextCursor,this.notModified=false});
  final List<LibraryCourseView> courses;
  final String etag;
  final String? nextCursor;
  final bool notModified;
}

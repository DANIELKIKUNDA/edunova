import 'package:edunova/src/features/library/application/library_repository.dart';
import 'package:edunova/src/features/library/domain/library.dart';
import 'package:flutter_test/flutter_test.dart';

LibraryCourseView course(String id, {String title = 'Anatomie'}) => LibraryCourseView(
  id: id,
  facultyDomain: 'Médecine',
  program: 'Médecine humaine',
  level: 'BAC1',
  semester: 'S1',
  title: title,
  slug: id,
  description: '',
  premiumRequired: false,
  updatedAt: DateTime.utc(2026, 9, 21),
);

class FakeLocalLibrary implements LibraryLocalRepository {
  String? knownEtag;
  int replacements = 0;
  List<LibraryCourseView> stored = [];

  @override
  Stream<List<LibraryCourseView>> watchCourses() => Stream.value(stored);

  @override
  Future<String?> catalogEtag(String cacheKey) async => knownEtag;

  @override
  Future<void> replaceCatalogScope(List<LibraryCourseView> courses, {required String cacheKey, String? facultyDomain, String? program, String? level, String? semester, required String etag}) async {
    replacements++;
    stored = List.of(courses);
    knownEtag = etag;
  }

  @override
  Future<void> saveManifest(LibraryManifest manifest) async {}

  @override
  Future<void> setCourseFollowed(String courseId, bool followed) =>
      throw UnimplementedError('Catalog refresh does not change followed courses');

  @override
  Stream<List<LibraryResourceView>> watchResources(String versionId) => const Stream.empty();
}

class FakeRemoteLibrary implements LibraryRemoteGateway {
  FakeRemoteLibrary(this.pages);
  final List<LibraryCatalogPage> pages;
  int calls = 0;

  @override
  Future<LibraryCatalogPage> loadCatalogPage({String? facultyDomain, String? program, String? level, String? semester, String? cursor, String? ifNoneMatch, int limit = 200}) async {
    final i = calls++;
    return pages[i];
  }

  @override
  Future<LibraryManifest> loadManifest(String courseId) => throw UnimplementedError();
}

void main() {
  test('complete paginated catalog is reconciled atomically', () async {
    final local = FakeLocalLibrary();
    final remote = FakeRemoteLibrary([
      LibraryCatalogPage(courses: [course('c1')], etag: 'etag-a', nextCursor: 'cursor-2'),
      LibraryCatalogPage(courses: [course('c2', title: 'Physiologie')], etag: 'etag-a'),
    ]);
    final count = await RefreshLibraryCatalog(local, remote)(facultyDomain: 'Médecine');
    expect(count, 2);
    expect(local.replacements, 1);
    expect(local.stored.map((e) => e.id), ['c1', 'c2']);
    expect(local.knownEtag, 'etag-a');
  });

  test('etag change during pagination keeps previous cache untouched', () async {
    final local = FakeLocalLibrary()..stored = [course('old')];
    final remote = FakeRemoteLibrary([
      LibraryCatalogPage(courses: [course('c1')], etag: 'etag-a', nextCursor: 'cursor-2'),
      LibraryCatalogPage(courses: [course('c2')], etag: 'etag-b'),
    ]);
    expect(
      () => RefreshLibraryCatalog(local, remote)(facultyDomain: 'Médecine'),
      throwsA(isA<StateError>()),
    );
    expect(local.replacements, 0);
    expect(local.stored.single.id, 'old');
  });

  test('304 does not rewrite local catalog', () async {
    final local = FakeLocalLibrary()..knownEtag = 'etag-a';
    final remote = FakeRemoteLibrary([
      const LibraryCatalogPage(courses: [], etag: 'etag-a', notModified: true),
    ]);
    final count = await RefreshLibraryCatalog(local, remote)();
    expect(count, 0);
    expect(local.replacements, 0);
  });
}

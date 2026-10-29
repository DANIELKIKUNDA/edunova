import '../../features/identity/infrastructure/secure_session_store.dart';

/// Repository-level defense in depth for an installation with a durable owner.
/// Ownerless offline-first installations are handled by bootstrap's legacy scan.
class LocalAccountAccess {
  LocalAccountAccess({SecureSessionStore? store}) : _store = store ?? SecureSessionStore();
  final SecureSessionStore _store;

  Future<void> assertReadable() async {
    final owner = await _store.ownerAccountId();
    if (owner == null) return; // Clean, anonymous offline-first installation.
    final session = await _store.read();
    if (session == null || session.accountId != owner) {
      throw StateError('local_data_requires_owner_authentication');
    }
  }

  /// Private projections must have an identified, authenticated owner.
  Future<void> assertOwned() async {
    final owner = await _store.ownerAccountId();
    if (owner == null) {
      throw StateError('local_private_data_owner_unknown');
    }
    await assertReadable();
  }

  /// Captures a session generation. Check again before committing a transaction.
  int captureRevision() => SecureSessionStore.sessionRevision;

  Future<void> assertUnchanged(int revision, {bool owned = false}) async {
    if (revision != SecureSessionStore.sessionRevision) {
      throw StateError('local_session_changed_during_operation');
    }
    if (owned) {
      await assertOwned();
    } else {
      await assertReadable();
    }
    if (revision != SecureSessionStore.sessionRevision) {
      throw StateError('local_session_changed_during_operation');
    }
  }

  Stream<T> protect<T>(Stream<T> source, {bool owned = true}) async* {
    final revision = captureRevision();
    await assertUnchanged(revision, owned: owned);
    await for (final value in source) {
      await assertUnchanged(revision, owned: owned);
      yield value;
    }
  }
}

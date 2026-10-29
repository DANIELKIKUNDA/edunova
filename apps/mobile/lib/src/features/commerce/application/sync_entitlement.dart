import 'commerce_repository.dart';

class SyncEntitlement {
  const SyncEntitlement({required this.local, required this.remote});
  final CommerceRepository local;
  final CommerceRemoteGateway remote;

  Future<void> call() async {
    final entitlement = await remote.getEntitlement();
    final receipts = await remote.getReceipts();
    await local.saveEntitlement(entitlement);
    await local.replaceReceipts(receipts);
  }
}

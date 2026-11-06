import '../../../core/database/app_database.dart';
import '../application/delivery_repository.dart';
import 'offline_resource_store_stub.dart'
  if (dart.library.io) 'offline_resource_store_native.dart'
  if (dart.library.html) 'offline_resource_store_web.dart' as impl;

OfflineResourceStore createOfflineResourceStore(AppDatabase db)=>impl.createOfflineResourceStore(db);

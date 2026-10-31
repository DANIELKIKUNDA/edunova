import 'dart:io';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

/// Legacy native downloads live outside SQLite. Never silently transfer them
/// to a new account when the installation owner cannot be established.
Future<bool> hasUnownedOfflineFiles() async {
  final root = await getApplicationSupportDirectory();
  final directory = Directory(p.join(root.path, 'offline_library'));
  if (!await directory.exists()) return false;
  return !await directory.list(followLinks: false).isEmpty;
}

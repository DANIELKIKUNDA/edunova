import 'package:drift/drift.dart';
import 'package:drift/wasm.dart';

QueryExecutor openConnection() => DatabaseConnection.delayed(
      Future(() async {
        final result = await WasmDatabase.open(
          databaseName: 'edunova_local',
          sqlite3Uri: Uri.parse('sqlite3.wasm'),
          driftWorkerUri: Uri.parse('drift_worker.js'),
        );

        return result.resolvedExecutor;
      }),
    );

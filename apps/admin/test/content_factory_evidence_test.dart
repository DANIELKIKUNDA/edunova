import 'dart:convert';
import 'package:edunova_admin/src/features/editorial/content_factory_page.dart';
import 'package:edunova_admin/src/features/editorial/editorial_api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  testWidgets('review opens the selected run and exposes selectable source pages and quote', (tester) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(1600, 1200);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    var detailRequests = 0;
    final client = MockClient((request) async {
      if (request.url.path == '/v1/content-factory/runs') {
        return http.Response(jsonEncode([
          {'id': 'run-evidence-123', 'state': 'ready_for_review', 'quality_score': 90, 'pipeline_version': 'test-pipeline'},
        ]), 200, headers: {'content-type': 'application/json; charset=utf-8'});
      }
      expect(request.url.path, '/v1/content-factory/runs/run-evidence-123');
      detailRequests++;
      return http.Response(jsonEncode({
        'id': 'run-evidence-123', 'state': 'ready_for_review', 'quality_score': 90,
        'assets': [{'id': 'asset-1', 'kind': 'summary', 'title': 'Source-backed summary', 'content': 'Generated text', 'confidence': .9}],
        'evidence': [{'asset_id': 'asset-1', 'page_start': 2, 'page_end': 3, 'quote': 'Exact source excerpt'}],
      }), 200, headers: {'content-type': 'application/json; charset=utf-8'});
    });
    addTearDown(client.close);
    // Factory extension methods require interception at the HTTP boundary.
    // No live network is used by this fixture.
    await http.runWithClient(() async {
      final api = EditorialApi('http://unused.invalid');
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: ContentFactoryPage(api: api))));
      await tester.pumpAndSettle();
      await tester.tap(find.textContaining('Run ').first);
      await tester.pumpAndSettle();
      expect(detailRequests, 1);
      await tester.tap(find.text('Source-backed summary'));
      await tester.pumpAndSettle();
      expect(find.text('Preuve source · p. 2–3'), findsOneWidget);
      expect(find.byWidgetPredicate((widget) => widget is SelectableText && widget.data == 'Exact source excerpt'), findsOneWidget);
      expect(tester.takeException(), isNull);
    }, () => client);
  });
}

import 'package:edunova_admin/src/features/editorial/content_factory_page.dart';
import 'package:edunova_admin/src/features/editorial/editorial_api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class EvidenceApi extends EditorialApi {
  EvidenceApi() : super('http://unused.invalid');
  int detailRequests = 0;
  @override
  Future<List<dynamic>> factoryRuns() async => [
    {'id': 'run-evidence-123', 'state': 'ready_for_review', 'quality_score': 90, 'pipeline_version': 'test-pipeline'},
  ];
  @override
  Future<Map<String, dynamic>> factoryRun(String id) async {
    detailRequests++;
    return {
      'id': id, 'state': 'ready_for_review', 'quality_score': 90,
      'assets': [{'id': 'asset-1', 'kind': 'summary', 'title': 'Source-backed summary', 'content': 'Generated text', 'confidence': .9}],
      'evidence': [{'asset_id': 'asset-1', 'page_start': 2, 'page_end': 3, 'quote': 'Exact source excerpt'}],
    };
  }
}

void main() {
  testWidgets('review opens the selected run and exposes selectable source pages and quote', (tester) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(1600, 1200);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final api = EvidenceApi();
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: ContentFactoryPage(api: api))));
    await tester.pumpAndSettle();
    await tester.tap(find.textContaining('Run ').first);
    await tester.pumpAndSettle();
    expect(api.detailRequests, 1);
    await tester.tap(find.text('Source-backed summary'));
    await tester.pumpAndSettle();
    expect(find.text('Preuve source · p. 2–3'), findsOneWidget);
    expect(find.byWidgetPredicate((widget) => widget is SelectableText && widget.data == 'Exact source excerpt'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

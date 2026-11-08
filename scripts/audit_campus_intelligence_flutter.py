"""Limited static checks of the Phase 14/15 Flutter bridge (NOT a Dart compiler).

Executes without Flutter. Never equate passing this with flutter analyze/test.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'apps/mobile/lib/src/features/campus_intelligence'
API = BASE / 'infrastructure/campus_intelligence_gateway.dart'
PANEL = BASE / 'presentation/institution_intelligence_page.dart'
TEACHER = BASE / 'presentation/pedagogical_governance_panel.dart'
ARCHIVE = BASE / 'presentation/institutional_archive_panel.dart'
CAMPUS = ROOT / 'apps/mobile/lib/src/features/campus/presentation/campus_page.dart'
SOURCE = API.read_text()
UI = PANEL.read_text()


checks = {
    'gateway_is_authenticated': '_auth()' in SOURCE and "'Authorization': 'Bearer" in SOURCE,
    'gateway_forbids_cache': "'Cache-Control': 'no-store'" in SOURCE,
    'gateway_has_route_id_validation': "^[a-zA-Z0-9_-]{1,128}$" in SOURCE,
    'gateway_has_objective_report': 'objectiveReport(' in SOURCE,
    'gateway_has_create_objective': 'registerObjective(' in SOURCE,
    'gateway_has_question_mapping': 'mapQuestion(' in SOURCE,
    'gateway_has_blueprint_binding': 'bindBlueprint(' in SOURCE,
    'gateway_has_archives': 'snapshotHistory(' in SOURCE,
    'gateway_has_archive_capture': 'captureSnapshot(' in SOURCE,
    'gateway_has_archival_comparison': 'archiveComparison(' in SOURCE,
    'gateway_csv_has_bound': 'body.length > 262144' in SOURCE,
    'gateway_does_not_write_jury': '/jury/' not in SOURCE and '/gradebook/' not in SOURCE,
    'frontend_rechecks_membership': "_gateway.institutions()" in UI and "membership['state'] != 'active'" in UI,
    'frontend_handles_auditor': "'auditor'" in UI and "'auditor'" in CAMPUS.read_text(),
    'frontend_teacher_panel_linked': 'PedagogicalGovernancePanel(' in UI,
    'frontend_archive_panel_linked': 'InstitutionalArchivePanel(' in UI,
    'teacher_mutations_have_server_refresh': 'await widget.gateway.objectiveReport' in TEACHER.read_text(),
    'archive_mutation_requires_confirmation': "if (confirmed != true" in ARCHIVE.read_text(),
    'archive_ignores_payload': "['payload']" not in ARCHIVE.read_text(),
    'archive_no_file_write': not any(x in ARCHIVE.read_text() for x in ('File(', 'Clipboard.', 'SharedPreferences', 'writeAsString')),
    'auditor_capture_hidden': "allowCapture: _role != 'auditor'" in UI and 'if (widget.allowCapture)' in ARCHIVE.read_text(),
    'auditor_mutation_denied_by_backend': 'institutional_analytics_auditor_read_only' in (ROOT / 'services/api/app/modules/institutional_analytics/application/service.py').read_text(),
    'frontend_rebinds_on_tenant_switch': 'void didUpdateWidget(covariant InstitutionIntelligencePage' in UI
        and 'oldWidget.institutionId != widget.institutionId' in UI,
    'frontend_request_generation_guards': all(x in UI for x in
        ('request != _teacherRequest', 'request != _executiveRequest', 'request != _comparisonRequest')),
    'frontend_revocation_clears_aggregates': '_invalidateOnAccessDenial' in UI
        and '_teacher = null; _reconciliation = null;' in UI
        and '_executive = null; _comparison = null;' in UI,
    'frontend_rejects_ambiguous_ids': '_requireUniqueIds' in UI,
    'archive_scope_change_clears_csv': '_previewCsv = null' in ARCHIVE.read_text()
        and 'oldWidget.allowCapture != widget.allowCapture' in ARCHIVE.read_text(),
    'archive_permission_downgrade_blocks_capture': 'generation != _generation ||' in ARCHIVE.read_text()
        and '!widget.allowCapture) return;' in ARCHIVE.read_text(),
    'archive_access_denial_purges_snapshot_state': '_clearOnAccessDenial' in ARCHIVE.read_text(),
    'sensitive_screen_clears_when_backgrounded': 'with WidgetsBindingObserver' in UI
        and 'void didChangeAppLifecycleState(AppLifecycleState state)' in UI
        and 'WidgetsBinding.instance.removeObserver(this)' in UI,
    'csv_preview_not_selectable': 'SelectableText(' not in ARCHIVE.read_text()
        and 'Text(_previewCsv!' in ARCHIVE.read_text(),
    'new_widget_race_tests_present': all((ROOT / 'apps/mobile/test' / name).exists() for name in (
        'campus_intelligence_tenant_transition_widget_test.dart',
        'campus_intelligence_archive_scope_widget_test.dart',
    )),
    'dart_tests_present': all((ROOT / 'apps/mobile/test' / name).exists() for name in (
        'campus_intelligence_gateway_test.dart',
        'campus_intelligence_access_widget_test.dart',
        'campus_intelligence_governance_gateway_test.dart',
        'campus_intelligence_completion_widget_test.dart',
    )),
}
for name, result in checks.items():
    print(f'{"PASS" if result else "FAIL"}: {name}')
assert all(checks.values()), 'One or more frontend static checks failed'
print(f'Static contract checks: {len(checks)}/{len(checks)} PASS (not Flutter certification)')

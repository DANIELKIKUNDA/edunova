from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
API=(ROOT/'apps/admin/lib/src/features/editorial/editorial_api.dart').read_text()
SHELL=(ROOT/'apps/admin/lib/src/features/platform/platform_shell.dart').read_text()

def test_platform_mutation_endpoints_wired():
    assert "'/v1/platform/members/${Uri.encodeComponent(accountId)}'" in API
    assert "'/v1/platform/members/${Uri.encodeComponent(accountId)}/deactivate'" in API
    assert "'expected_version':expectedVersion" in API
    assert "'expected_version':expectedVersion" not in SHELL

def test_role_editor_restricted_to_permissioned_members():
    assert "contains('platform.roles.manage')" in SHELL
    assert 'if(members!=null)' in SHELL
    assert 'manageMember(m)' in SHELL

def test_conflict_and_destructive_action_handled():
    assert 'e.isConflict' in SHELL
    assert 'Confirmer la désactivation' in SHELL
    assert 'deactivatePlatformMember' in SHELL

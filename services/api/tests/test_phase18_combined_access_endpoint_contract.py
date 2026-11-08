from pathlib import Path

from app.modules.commerce.api.router import combined_access


def test_endpoint_is_authenticated():
    from inspect import signature
    assert 'auth' in signature(combined_access).parameters


def test_endpoint_uses_real_membership_and_license():
    source = Path(__file__).parents[1] / 'app/modules/commerce/api/router.py'
    code = source.read_text().split('def combined_access(', 1)[1].split('@router.get("/receipts")', 1)[0]
    for guard in ('runtime.campus_repo.membership(', 'MembershipState.ACTIVE',
                  'CampusRole.STUDENT', 'InstitutionState.ACTIVE',
                  'license.permits(', 'runtime.commerce.snapshot('):
        assert guard in code


def test_no_client_supplied_authorization_flags():
    from inspect import signature
    assert set(signature(combined_access).parameters) == {'institution_id', 'auth'}

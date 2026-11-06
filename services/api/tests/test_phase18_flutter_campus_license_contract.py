from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_campus_uses_scoped_rights_from_authenticated_api():
    providers = (ROOT / 'apps/mobile/lib/src/core/di/providers.dart').read_text()
    gateway = (ROOT / 'apps/mobile/lib/src/features/commerce/infrastructure/api_commerce_gateway.dart').read_text()
    assert 'FutureProvider.autoDispose.family<CombinedAccessView, String>' in providers
    assert 'getCombinedAccess(institutionId: institutionId)' in providers
    assert "'institution_id': institutionId.trim()" in gateway
    assert 'options: await _authOptions()' in gateway


def test_campus_does_not_claim_access_on_network_error_or_inactive_membership():
    page = (ROOT / 'apps/mobile/lib/src/features/campus/presentation/campus_page.dart').read_text()
    assert 'if (active && id.isNotEmpty)' in page
    assert '_CampusLicenseStatus(institutionId: id)' in page
    assert 'Licence Campus non vérifiée' in page
    assert 'rights.campusAccess ?' in page
    assert 'Votre accès personnel Gratuit ou Premium reste indépendant.' in page
    assert 'campusCombinedAccessProvider(institutionId)' in page

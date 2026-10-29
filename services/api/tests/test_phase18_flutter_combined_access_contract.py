from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_combined_access_uses_authenticated_server_endpoint():
    src = (ROOT / "apps/mobile/lib/src/features/commerce/infrastructure/api_commerce_gateway.dart").read_text()
    assert "'/v1/commerce/combined-access'" in src
    assert "options: await _authOptions()" in src
    assert "CombinedAccessView.fromJson" in src


def test_premium_ui_does_not_infer_campus_membership():
    src = (ROOT / "apps/mobile/lib/src/features/commerce/presentation/premium_page.dart").read_text()
    assert "ref.watch(combinedAccessProvider)" in src
    assert "aucune affiliation n’est déduite" in src
    assert "ref.invalidate(combinedAccessProvider)" in src

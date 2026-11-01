from historical_audit_contracts import release_at_least
from pathlib import Path
r=Path(__file__).resolve().parents[1]
p=(r/'apps/admin/lib/src/features/editorial/content_factory_page.dart').read_text()
checks={
'admin 0.14.2+22':release_at_least(r, 'admin', '0.14.2+22'),
'mobile 0.14.2+22':release_at_least(r, 'mobile', '0.14.2+22'),
'api 0.14.2':release_at_least(r, 'api', '0.14.2'),
'kpi responsive':'_KpiGrid' in p and 'crossAxisCount:cols' in p,
'search':'Rechercher un run' in p,
'state filters':'À relire' in p and 'Bloqués' in p,
'quality sorting':'Qualité décroissante' in p and 'À surveiller' in p,
'master detail':'_DesktopDetail' in p and 'width >= 1180' in p,
'mobile review sheet':'showModalBottomSheet' in p and 'DraggableScrollableSheet' in p,
'review tabs':'Artefacts' in p and 'Qualité' in p and 'Traçabilité' in p,
'source evidence':'Preuve source' in p and "page_start" in p and "quote" in p,
'asset filtering':'assetFilter' in p,
'loading state':'CircularProgressIndicator' in p,
'empty state':'_EmptyFactory' in p,
'no results state':'_NoResults' in p,
'error retry':'Connexion interrompue' in p and 'Réessayer' in p,
'human governance':'Validation humaine obligatoire avant publication' in p,
'no auto publish':'Aucune publication automatique' in p,
'accessibility semantics':'Semantics(' in p,
'selectable evidence':'SelectableText' in p,
'pull refresh':'RefreshIndicator' in p,
'doc':(r/'docs/LOT13_UIUX_PREMIUM_FINAL_v0.14.2.md').exists(),
'acceptance':(r/'docs/certification/LOT13_UIUX_FINAL_ACCEPTANCE_v0.14.2.md').exists(),
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"{len(checks)-len(failed)}/{len(checks)} PASS")
raise SystemExit(1 if failed else 0)

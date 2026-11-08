from historical_audit_contracts import release_at_least
from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'api 0.14.1':release_at_least(r, 'api', '0.14.1'),
'admin 0.14.1+21':release_at_least(r, 'admin', '0.14.1+21'),
'mobile 0.14.1+21':release_at_least(r, 'mobile', '0.14.1+21'),
'quality module':(r/'services/api/app/modules/content_factory/application/quality.py').exists(),
'quote grounding':'evidence_quote_grounded' in (r/'services/api/app/modules/content_factory/application/quality.py').read_text(),
'hash integrity':'evidence_hash_integrity' in (r/'services/api/app/modules/content_factory/application/quality.py').read_text(),
'numeric grounding':'numeric_claim_grounding' in (r/'services/api/app/modules/content_factory/application/quality.py').read_text(),
'duplicate guard':'semantic_duplicate_guard' in (r/'services/api/app/modules/content_factory/application/quality.py').read_text(),
'review package':'review-package' in (r/'services/api/app/modules/content_factory/api/router.py').read_text(),
'publication blocked':"'publication_allowed':False" in (r/'services/api/app/modules/content_factory/api/router.py').read_text(),
'cancel endpoint':"/cancel'" in (r/'services/api/app/modules/content_factory/api/router.py').read_text(),
'source compare UI':all(token in (r/'apps/admin/lib/src/features/editorial/content_factory_page.dart').read_text() for token in ['Preuve source · p.', "ev['page_start']", "ev['page_end']", "ev['quote']", 'SelectableText']),
'final acceptance':(r/'docs/certification/LOT13_FINAL_ACCEPTANCE_v0.14.1.md').exists(),
'no TODO core':all(x not in '\n'.join(p.read_text(errors='ignore') for p in (r/'services/api/app/modules/content_factory').rglob('*.py')) for x in ('TODO','FIXME','NotImplementedError')),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

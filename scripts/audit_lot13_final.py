from pathlib import Path
r=Path(__file__).resolve().parents[1]
checks={
'api 0.14.1':'version="0.14.1"' in (r/'services/api/app/main.py').read_text(),
'admin 0.14.1+21':'version: 0.14.1+21' in (r/'apps/admin/pubspec.yaml').read_text(),
'mobile 0.14.1+21':'version: 0.14.1+21' in (r/'apps/mobile/pubspec.yaml').read_text(),
'quality module':(r/'services/api/app/modules/content_factory/application/quality.py').exists(),
'quote grounding':'evidence_quote_grounded' in (r/'services/api/app/modules/content_factory/application/quality.py').read_text(),
'hash integrity':'evidence_hash_integrity' in (r/'services/api/app/modules/content_factory/application/quality.py').read_text(),
'numeric grounding':'numeric_claim_grounding' in (r/'services/api/app/modules/content_factory/application/quality.py').read_text(),
'duplicate guard':'semantic_duplicate_guard' in (r/'services/api/app/modules/content_factory/application/quality.py').read_text(),
'review package':'review-package' in (r/'services/api/app/modules/content_factory/api/router.py').read_text(),
'publication blocked':"'publication_allowed':False" in (r/'services/api/app/modules/content_factory/api/router.py').read_text(),
'cancel endpoint':"/cancel'" in (r/'services/api/app/modules/content_factory/api/router.py').read_text(),
'source compare UI':'Preuve source p.' in (r/'apps/admin/lib/src/features/editorial/content_factory_page.dart').read_text(),
'final acceptance':(r/'docs/certification/LOT13_FINAL_ACCEPTANCE_v0.14.1.md').exists(),
'no TODO core':all(x not in '\n'.join(p.read_text(errors='ignore') for p in (r/'services/api/app/modules/content_factory').rglob('*.py')) for x in ('TODO','FIXME','NotImplementedError')),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print(f"{sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

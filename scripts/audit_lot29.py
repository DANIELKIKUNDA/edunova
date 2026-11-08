from pathlib import Path
checks={
'commercial domain':Path('services/api/app/modules/commerce/domain/commercial.py').exists(),
'commercial service':Path('services/api/app/modules/commerce/application/commercial_service.py').exists(),
'migration 0049':Path('services/api/migrations/0049_commerce_mobile_money_campus_licensing_v0_30_0.sql').exists(),
'lot29 tests':Path('services/api/tests/test_commerce_lot29.py').exists(),
'ADR 049':Path('docs/architecture/ADR-049-commerce-campus-licensing-revenue-sharing.md').exists(),
'webhook signature':'verify_webhook' in Path('services/api/app/modules/commerce/api/router.py').read_text(),
'idempotency':'Idempotency-Key' in Path('services/api/app/modules/commerce/api/router.py').read_text(),
'campus license endpoint':"/campus/{institution_id}/licenses" in Path('services/api/app/modules/commerce/api/router.py').read_text(),
'revenue sharing':'RevenueShareRule' in Path('services/api/app/modules/commerce/domain/commercial.py').read_text(),
'ledger':'commercial_ledger' in Path('services/api/migrations/0049_commerce_mobile_money_campus_licensing_v0_30_0.sql').read_text(),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
print(f"LOT29 AUDIT: {sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

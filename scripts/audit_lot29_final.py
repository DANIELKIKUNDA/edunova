from pathlib import Path
checks={
'provider webhook signature':'verify_webhook' in Path('services/api/app/modules/commerce/api/router.py').read_text(),
'webhook dedupe':'WebhookInboxRow' in Path('services/api/app/modules/commerce/infrastructure/sqlalchemy_repo.py').read_text(),
'atomic settlement':'with_for_update' in Path('services/api/app/modules/commerce/infrastructure/sqlalchemy_repo.py').read_text(),
'late terminal protection':'must never downgrade a settled payment' in Path('services/api/app/modules/commerce/infrastructure/sqlalchemy_repo.py').read_text(),
'reversible subscription grants':'reversed_at' in Path('services/api/app/modules/commerce/infrastructure/sqlalchemy_repo.py').read_text(),
'campus licenses':'CampusLicense' in Path('services/api/app/modules/commerce/domain/commercial.py').read_text(),
'license lifecycle':'effective_state' in Path('services/api/app/modules/commerce/domain/commercial.py').read_text(),
'commercial ledger':'CommercialLedgerRow' in Path('services/api/app/modules/commerce/infrastructure/sqlalchemy_repo.py').read_text(),
'business event uniqueness':'uq_commercial_ledger_business_event' in Path('services/api/app/modules/commerce/infrastructure/sqlalchemy_repo.py').read_text(),
'revenue sharing':'record_revenue_share' in Path('services/api/app/modules/commerce/application/commercial_service.py').read_text(),
'compensating refunds':'record_refund' in Path('services/api/app/modules/commerce/application/commercial_service.py').read_text(),
'settlement close':'close_settlement' in Path('services/api/app/modules/commerce/application/commercial_service.py').read_text(),
'settlement paid':'mark_settlement_paid' in Path('services/api/app/modules/commerce/application/commercial_service.py').read_text(),
'settlement uniqueness':'uq_partner_settlement_period' in Path('services/api/app/modules/commerce/infrastructure/sqlalchemy_repo.py').read_text(),
'provider reconciliation':'reconcile_provider' in Path('services/api/app/modules/commerce/application/commercial_service.py').read_text(),
'campus RBAC':'ADMIN_ROLES' in Path('services/api/app/modules/commerce/application/commercial_service.py').read_text(),
'migration 0049':Path('services/api/migrations/0049_commerce_mobile_money_campus_licensing_v0_30_0.sql').exists(),
'final certification doc':Path('docs/certification/LOT29_v0.30.2_FINAL.md').exists(),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
print(f"LOT29 FINAL AUDIT: {sum(checks.values())}/{len(checks)} PASS")
raise SystemExit(0 if all(checks.values()) else 1)

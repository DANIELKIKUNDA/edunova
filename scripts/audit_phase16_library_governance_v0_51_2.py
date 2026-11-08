"""Static code-wiring checks only. These DO NOT compile or execute Flutter."""
from pathlib import Path
root = Path(__file__).resolve().parent.parent
checks = {
    'Migration 0088 renewal field': ('services/api/migrations/0088_campus_library_circulation_policy_v0_51_2.sql', 'ADD COLUMN renewal_count'),
    'Migration 0088 data constraint': ('services/api/migrations/0088_campus_library_circulation_policy_v0_51_2.sql', 'CHECK (renewal_count >= 0 AND renewal_count <= 2)'),
    'Migration 0088 due index': ('services/api/migrations/0088_campus_library_circulation_policy_v0_51_2.sql', 'ix_campus_library_active_borrower_due'),
    'DB field renewal count': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'renewal_count: Mapped[int]'),
    'DB check constraint': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'ck_campus_library_loan_renewals'),
    'Borrower transactional advisory lock': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'pg_advisory_xact_lock'),
    'Borrower quota': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'campus_library_borrower_quota_exceeded'),
    'Borrower overdue block': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'campus_library_overdue_loans_block_borrow'),
    'Renew limit': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'campus_library_renewal_limit_reached'),
    'Renew CAS': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'current.row_version != version'),
    'Renew borrower scoped': ('services/api/app/modules/campus_services/infrastructure/physical_library_repo.py', 'PhysicalLoanRow.borrower_account_id == borrower'),
    'API renew endpoint': ('services/api/app/modules/campus_services/api/physical_library_router.py', "'/institutions/{institution_id}/library/loans/{loan_id}/renew'"),
    'API overdue flag': ('services/api/app/modules/campus_services/api/physical_library_router.py', "'overdue':"),
    'API server-controlled renewal visibility': ('services/api/app/modules/campus_services/api/physical_library_router.py', "'can_renew': v.id in eligible"),
    'Service audit on renewal': ('services/api/app/modules/campus_services/application/physical_library_service.py', 'campus.library.loan.renewed'),
    'Flutter authenticated gateway': ('apps/mobile/lib/src/features/campus_services/infrastructure/campus_services_gateway.dart', 'renewPhysicalLoan(String iid'),
    'Flutter renewal interface': ('apps/mobile/lib/src/features/campus_services/presentation/physical_library_page.dart', "Prolonger de ${_policy?['renewal_days'] ?? 14} jours"),
    'Flutter deadline warning': ('apps/mobile/lib/src/features/campus_services/presentation/physical_library_page.dart', 'EN RETARD'),
    'Flutter contract test authored': ('apps/mobile/test/campus_services_gateway_test.dart', 'Prolongations : identité issue du token'),
    'Backend adversarial tests authored': ('services/api/tests/test_phase16_library_governance_v0_51_2.py', 'test_borrower_alone_can_renew_and_tenant_mismatch_hides_loan'),
}
fail=[]
for name,(path,needle) in checks.items():
    ok=needle in (root/path).read_text(encoding='utf-8')
    print(f'{"PASS" if ok else "FAIL"} {name}')
    if not ok:fail.append(name)
print(f'STATIC WIRING: {len(checks)-len(fail)}/{len(checks)}')
if fail:raise SystemExit(1)

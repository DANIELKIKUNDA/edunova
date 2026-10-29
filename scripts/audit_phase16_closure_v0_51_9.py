"""Non-compiler structural checks for Phase 16 release; NOT a Flutter test."""
from pathlib import Path
root=Path(__file__).resolve().parent.parent
files={
 'service': 'services/api/app/modules/campus_services/application/service.py',
 'repo': 'services/api/app/modules/campus_services/infrastructure/sqlalchemy_repo.py',
 'alumni': 'services/api/app/modules/campus_services/application/alumni_service.py',
 'alumni_repo': 'services/api/app/modules/campus_services/infrastructure/alumni_repo.py',
 'router': 'services/api/app/modules/campus_services/api/router.py',
 'mobile': 'apps/mobile/lib/src/features/campus/presentation/campus_page.dart',
 'alumni_screen': 'apps/mobile/lib/src/features/campus_services/presentation/campus_alumni_page.dart',
 'room_screen': 'apps/mobile/lib/src/features/campus_services/presentation/campus_academic_resources_page.dart',
 'gateway': 'apps/mobile/lib/src/features/campus_services/infrastructure/campus_services_gateway.dart',
 'flutter_test': 'apps/mobile/test/campus_academic_alumni_gateway_test.dart',
 'backend_test': 'services/api/tests/test_phase16_closure_v0_51_9.py',
 'ci': '.github/workflows/ci.yml',
}
source={key:(root/rel).read_text() for key,rel in files.items()}
checks={
 'unassigned_staff_guard': ('service','self._staff(account, institution)'),
 'future_unassigned_calendar': ('repo',"CalendarEventRow.state == 'scheduled'"),
 'future_unassigned_teaching': ('repo',"TeachingSessionRow.state == 'planned'"),
 'reconciliation_count': ('repo','calendar_count=calendar_count, teaching_count=teaching_count'),
 'alumni_account_scoping': ('alumni_repo','AlumniProfileRow.account_id == account'),
 'verified_only_alumni': ('alumni_repo',"AlumniProfileRow.status == 'verified'"),
 'alumni_membership_revocation': ('alumni','MembershipState.REVOKED, MembershipState.SUSPENDED'),
 'alumni_tenant_active': ('alumni','InstitutionState.ACTIVE'),
 'alumni_cannot_edit_expired_membership': ('alumni','self._member(account, institution)'),
 'alumni_no_dossier_reference': ('alumni','result.append({\'institution_id\': institution, \'name\': target.name})'),
 'academic_unassigned_route': ('router',"'/institutions/{institution_id}/academic-unassigned'"),
 'alumni_discovery_route': ('router',"'/alumni/my-institutions'"),
 'mobile_verified_alumni_entry': ('mobile','campusVerifiedAlumniProvider'),
 'alumni_readonly_expired': ('alumni_screen','_canApply ? FilledButton'),
 'room_unassigned_selector': ('room_screen','final candidates = <Map<String, String>>['),
 'tenant_screen_invalidation': ('room_screen','request != _revision'),
 'gateway_no_store': ('gateway',"'Cache-Control': 'no-store'"),
 'gateway_alumni_discovery': ('gateway',"'/v1/campus-services/alumni/my-institutions'"),
 'gateway_reconciliation': ('gateway',"'${_base(iid)}/academic-unassigned'"),
 'flutter_contract_test': ('flutter_test','Réconciliation des séances et découverte Alumni'),
 'backend_negative_test': ('backend_test','test_alumni_discovery_only_own_verified_not_suspended'),
 'ci_flutter_build': ('ci','flutter build web --release --no-pub'),
}
errors=[name for name,(key,needle) in checks.items() if needle not in source[key]]
for name in checks: print(('FAIL' if name in errors else 'PASS')+' '+name)
print(f'{len(checks)-len(errors)}/{len(checks)} checks (structural only)')
raise SystemExit(bool(errors))

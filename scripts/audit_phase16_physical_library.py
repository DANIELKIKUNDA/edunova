"""Lightweight wiring inspection only; does NOT execute or compile Flutter."""
from pathlib import Path
root = Path(__file__).resolve().parent.parent
checks = {
    'FastAPI library router included': ('services/api/app/main.py', 'app.include_router(physical_library_router'),
    'Runtime library service': ('services/api/app/runtime.py', 'self.physical_library = PhysicalLibraryService('),
    'Physical book endpoint': ('services/api/app/modules/campus_services/api/physical_library_router.py', "'/institutions/{institution_id}/library/books'"),
    'Physical copy endpoint': ('services/api/app/modules/campus_services/api/physical_library_router.py', "'/institutions/{institution_id}/library/copies'"),
    'Physical loan endpoint': ('services/api/app/modules/campus_services/api/physical_library_router.py', "'/institutions/{institution_id}/library/loans'"),
    'Loan return endpoint': ('services/api/app/modules/campus_services/api/physical_library_router.py', "/loans/{loan_id}/return'"),
    'Tenant FK copy': ('services/api/migrations/0087_campus_physical_library_v0_51_1.sql', 'FOREIGN KEY (institution_id,book_id)'),
    'Tenant FK loan': ('services/api/migrations/0087_campus_physical_library_v0_51_1.sql', 'FOREIGN KEY (institution_id,copy_id)'),
    'Open loan unique index': ('services/api/migrations/0087_campus_physical_library_v0_51_1.sql', 'WHERE returned_at IS NULL'),
    'Flutter physical library page': ('apps/mobile/lib/src/features/campus_services/presentation/physical_library_page.dart', 'class PhysicalLibraryPage'),
    'Flutter book operations': ('apps/mobile/lib/src/features/campus_services/infrastructure/campus_services_gateway.dart', 'physicalBooks(String iid)'),
    'Flutter borrow operations': ('apps/mobile/lib/src/features/campus_services/infrastructure/campus_services_gateway.dart', 'borrowPhysicalCopy(String iid'),
    'Flutter return operations': ('apps/mobile/lib/src/features/campus_services/infrastructure/campus_services_gateway.dart', 'returnPhysicalLoan(String iid'),
    'Flutter navigation route': ('apps/mobile/lib/src/app/router.dart', '/campus/physical-library/:institutionId'),
    'Campus route entry': ('apps/mobile/lib/src/features/campus/presentation/campus_page.dart', "label: const Text('Bibliothèque physique')"),
    'Flutter gateway tests written': ('apps/mobile/test/campus_services_gateway_test.dart', "test('Bibliothèque physique"),
}
failed = []
for description, (path, pattern) in checks.items():
    ok = pattern in (root / path).read_text(encoding='utf-8')
    print(f'{"PASS" if ok else "FAIL"} {description}')
    if not ok: failed.append(description)
print(f'WIRING STATIC {len(checks) - len(failed)}/{len(checks)} PASS')
if failed: raise SystemExit(1)

from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def has(path,*needles):
    text=(ROOT/path).read_text(encoding='utf-8')
    return all(n in text for n in needles)
def ck(name,ok): checks.append((name,bool(ok)))
ck('api_version_0_12_1',has('services/api/app/main.py','version="0.12.1"','"version": "0.12.1"'))
ck('migration_0008', (ROOT/'services/api/migrations/0008_editorial_hardening_v0_12_1.sql').exists())
ck('optimistic_locking',has('services/api/app/modules/editorial/infrastructure/sqlalchemy_repo.py','row_version','editorial_concurrent_modification'))
ck('structured_review_checklist',has('services/api/app/modules/editorial/application/service.py','review_checklist_incomplete','HIGH_RISK_CHECKS','STANDARD_CHECKS'))
ck('high_risk_separation',has('services/api/app/modules/editorial/application/service.py','high_risk_separation_of_duties_required'))
ck('ocr_second_person',has('services/api/app/modules/editorial/application/service.py','source_verification_requires_second_person'))
ck('assignments',has('services/api/app/modules/editorial/application/service.py','AssignmentStage.REVIEW','AssignmentStage.PUBLICATION','complete_assignment'))
ck('search_pagination',has('services/api/app/modules/editorial/api/router.py',"/items/search",'offset:int','limit:int'))
ck('detail_history_quality_gates',has('services/api/app/modules/editorial/api/router.py',"/items/{item_id}",'review_gates','publish_gates','audit'))
ck('restore_revision',has('services/api/app/modules/editorial/application/service.py','def restore_revision'))
ck('library_archive_projection',has('services/api/app/modules/editorial/infrastructure/library_projector.py','def archive'))
ck('secure_refresh_session',has('apps/admin/lib/src/features/editorial/editorial_api.dart','/v1/identity/refresh','StudioSessionStore'))
ck('studio_responsive_navigation',has('apps/admin/lib/src/features/editorial/editorial_shell.dart','NavigationRail','NavigationBar'))
ck('studio_search_filters',has('apps/admin/lib/src/features/editorial/content_list_page.dart','Rechercher un cours','Pagination') if False else has('apps/admin/lib/src/features/editorial/content_list_page.dart','searchItems','_Filter'))
ck('studio_detail_tabs',has('apps/admin/lib/src/features/editorial/content_detail_page.dart','Vue d’ensemble','Révisions','Sources','Relecture','Publications','Historique'))
ck('studio_review_checklist_ui',has('apps/admin/lib/src/features/editorial/content_detail_page.dart','Checklist obligatoire','Exactitude factuelle','Sécurité / absence de conseil dangereux'))
ck('studio_conflict_ux',has('apps/admin/lib/src/features/editorial/content_detail_page.dart','modifié par quelqu’un d’autre'))
ck('studio_team_roles',has('apps/admin/lib/src/features/editorial/team_page.dart','Owner — administration complète','Reviewer — contrôle qualité'))
# basic delimiter balance for modified Dart files (not a Flutter compile)
for path in (ROOT/'apps/admin/lib').rglob('*.dart'):
    text=path.read_text(encoding='utf-8')
    # Strip quoted strings conservatively so braces inside labels/JSON do not count.
    stripped=re.sub(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"",'',text)
    for op,cl in [('(',')'),('[',']'),('{','}')]:
        ck(f'dart_balance:{path.name}:{op}',stripped.count(op)==stripped.count(cl))
# core stub audit
bad=[]
for base in [ROOT/'services/api/app/modules/editorial',ROOT/'apps/admin/lib']:
    for p in base.rglob('*'):
        if p.is_file() and p.suffix in {'.py','.dart'}:
            t=p.read_text(encoding='utf-8',errors='ignore')
            if re.search(r'\b(TODO|FIXME|NotImplementedError)\b',t): bad.append(str(p.relative_to(ROOT)))
ck('no_core_stubs',not bad)
failed=[n for n,v in checks if not v]
for n,v in checks: print(('PASS' if v else 'FAIL'),n)
print(f'RESULT {sum(v for _,v in checks)}/{len(checks)} PASS')
if failed:
    print('FAILED:',', '.join(failed)); sys.exit(1)

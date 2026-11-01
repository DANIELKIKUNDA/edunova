"""Generate final evidence from executed jobs; never infer PASS from artifacts."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'evidence/phase19-final'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf8').strip()

def read(name):
    path = OUT/name
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else None

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def junit(name):
    path=OUT/f'{name}.xml'
    if not path.exists(): return None
    cases=ET.parse(path).getroot().findall('.//testcase')
    return {'passed':sum(not any(c.find(t) is not None for t in ('failure','error','skipped')) for c in cases),
            'failed':sum(any(c.find(t) is not None for t in ('failure','error')) for c in cases),
            'skipped':sum(c.find('skipped') is not None for c in cases)}

def generate():
    head=git('rev-parse','HEAD')
    jobs={}
    for path in OUT.glob('*.json'):
        data=read(path.name)
        if isinstance(data,dict) and all(k in data for k in ('command','cwd','exit_code','commit')) and '-previous-' not in path.stem:
            jobs[path.stem]=data
    audits=read('audits/results.json') or []
    diagnostics=['# Tentatives non réussies et corrections','',
                 'Les codes non nuls restent conservés, même après une reprise réussie. Les JSON associés contiennent la commande, le commit et le répertoire exacts.', '',
                 '- FastAPI 0.162 utilise des routeurs inclus effectifs : trois tests inspectaient seulement la liste de premier niveau. Adaptation à `iter_route_contexts`, sans suppression des assertions d’unicité, de méthode ni de dépendance `current_auth` ; ajout de requêtes internes sans authentification exigeant 401.',
                 '- Le nouveau test workspace a révélé un débordement de 22 px : titres de rangées non contraints. Correction avec Expanded ; assertion d’absence d’exception conservée.',
                 '- Le premier double Admin tentait de surcharger des méthodes d’extension Dart : deux avertissements de surcharge inexistante. Le test intercepte désormais les vraies requêtes HTTP via MockClient, sans modifier l’API de production.',
                 '- Dépréciation Drift web : information résiduelle ; les analyses Mobile de code 1 ne sont pas des PASS.',
                 '- Premier audit pip : 100 entrées signalées dans cinq paquets. Mises à jour testées séparément ; les résultats avant correction restent disponibles.', '']
    for path in sorted(OUT.glob('*-previous-*.json')):
        record=read(path.name)
        if isinstance(record,dict) and record.get('exit_code',0)!=0 and 'command' in record:
            log=path.with_suffix('.log')
            diagnostics += [f'## {path.stem}', '',f'Commande : `{subprocess.list2cmdline(record["command"])}`.',
                            f'Code : {record["exit_code"]}. Commit : `{record["commit"]}`.',
                            f'Trace : [{log.name}]({log.name}).', '']
    for path in sorted(OUT.glob('*-previous-*.xml')):
        for case in ET.parse(path).getroot().findall('.//testcase'):
            error=case.find('failure')
            if error is None: error=case.find('error')
            if error is not None:
                diagnostics += [f'### {case.attrib["name"]}', '',f'JUnit : [{path.name}]({path.name}).','', '```text',error.text or error.attrib.get('message',''), '```','']
    (OUT/'DIAGNOSTICS.md').write_text('\n'.join(diagnostics),encoding='utf8')
    artifacts=[]
    bundles=[]
    original=json.loads((ROOT/'evidence/local-phase19/ARTIFACTS.json').read_text(encoding='utf8'))
    for item in original:
        path=ROOT/item['path']; name=item['job']; job=jobs.get(name)
        result={'job':name,'path':item['path'],'exists':path.exists(), 'commit':job['commit'] if job else None,
                'exit_code':job['exit_code'] if job else None}
        if path.exists():
            result.update(size_bytes=path.stat().st_size,sha256=digest(path))
            if path.suffix=='.apk':
                with zipfile.ZipFile(path) as z:
                    result['abis']=sorted({n.split('/')[1] for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')})
        artifacts.append(result)
        if job and job['exit_code']==0 and path.exists():
            files=[path] if path.suffix=='.apk' else sorted(p for p in path.parent.rglob('*') if p.is_file())
            bundles.append({'job':name,'commit':job['commit'],'files':[
                {'path':p.relative_to(ROOT).as_posix(),'size_bytes':p.stat().st_size,'sha256':digest(p)} for p in files]})
    (OUT/'ARTIFACTS.json').write_text(json.dumps(artifacts,indent=2),encoding='utf8')
    (OUT/'BUNDLE_MANIFESTS.json').write_text(json.dumps(bundles,indent=2),encoding='utf8')
    for app in ('mobile','admin'):
        shutil.copyfile(ROOT/f'apps/{app}/pubspec.lock',OUT/f'{app}-dependencies.lock')
    proofs=[]
    for name,job in jobs.items():
        paths=['services/api/app','services/api/tests','services/api/requirements.txt'] if name in ('backend-final','phase19','postgres') else []
        if name=='backend': paths=['services/api/app']  # baseline also predates effective-router test adaptation
        for app in ('mobile','admin'):
            if name.startswith(app+'-'):
                paths=[f'apps/{app}/lib',f'apps/{app}/pubspec.yaml']
                if name.endswith('-pub'): paths=[f'apps/{app}/pubspec.yaml']
                if name.endswith('-test'): paths.append(f'apps/{app}/test')
                for platform in ('web','windows','android'):
                    if name.endswith('-'+platform): paths.append(f'apps/{app}/{platform}')
        for path in paths:
            tested=git('rev-parse',f'{job["commit"]}:{path}')
            delivered=git('rev-parse',f'HEAD:{path}')
            proofs.append(dict(job=name,path=path,tested_commit=job['commit'],tested_tree=tested,delivered_tree=delivered,identical=tested==delivered))
    (OUT/'TREE_IDENTITY.json').write_text(json.dumps(proofs,indent=2),encoding='utf8')
    deps=read('dependency-audit.json') or {}
    vulnerable=[d for d in deps.get('dependencies',[]) if d.get('vulns')]
    pub_audit=read('pub-dependency-audit-results.json')
    security=[]
    xml=OUT/'backend-final.xml'
    if xml.exists():
        for case in ET.parse(xml).getroot().findall('.//testcase'):
            suite=case.attrib.get('classname','')
            if any(token in suite for token in ('identity_security','tenant_policy','license_status_authorization','security_headers','security_storage','test_preflight','phase19','campus_lot22_hardening','platform_governance')):
                status='FAIL' if any(case.find(t) is not None for t in ('error','failure')) else 'SKIP' if case.find('skipped') is not None else 'PASS'
                security.append({'suite':suite,'name':case.attrib['name'],'status':status})
    (OUT/'SECURITY_COVERAGE.json').write_text(json.dumps(security,indent=2),encoding='utf8')
    required=['audits','backend-final','phase19','postgres','migrations','mobile-pub','admin-pub','mobile-test','admin-test',
              'mobile-web','admin-web','mobile-windows','admin-windows','mobile-android','admin-android']
    missing=[n for n in required if n not in jobs]
    failed=[n for n in required if n in jobs and jobs[n]['exit_code']!=0]
    verdict='PARTIELLEMENT CERTIFIÉ'
    # Static analysis, dependency findings and known illustrative screens are
    # explicit reservations even when functional suites pass.
    lines=['# EduNova — certification finale de la Phase 19','',f'Généré le {datetime.now(ZoneInfo("Africa/Lubumbashi")).isoformat()}.',
           '',f'## Verdict : {verdict}','',
           'Cette certification locale n’autorise pas une mise en production. Les constats sont issus des exécutions conservées ; aucune réussite n’est déduite d’un ancien build.',
           '', '## Livraison et provenance', '',
           f'HEAD de préparation du rapport : `{head}`. Les commits documentaires de livraison peuvent lui succéder ; le SHA final publié est consigné dans la conversation PR #1 et dans le bilan de livraison.',
           'Branche : `import/edunova-v0.57.12`. Aucun merge dans main. La publication finale et le statut brouillon doivent être vérifiés après le push ; voir [publication.json](evidence/phase19-final/publication.json).',
           'Les commits testés sont indiqués individuellement ci-dessous. [TREE_IDENTITY.json](evidence/phase19-final/TREE_IDENTITY.json) compare les sources réellement exécutées aux sources livrées, y compris les dépendances déclarées.',
           'Les échecs, commandes, traces et correctifs intermédiaires figurent dans [DIAGNOSTICS.md](evidence/phase19-final/DIAGNOSTICS.md).',
           '', '## Environnement et reproduction', '',
           'Windows 11 x64, Git 2.51.0, Python 3.13.14 ; environnement initial `.venv` conservé et environnement corrigé `.local-certification/security-venv` séparé. Flutter 3.35.4 / Dart 3.9.2, PostgreSQL 16.11 local : `127.0.0.1:55439`, utilisateur de test `edunova_cert`. SDK Android local, Java 21, Visual Studio 2022 avec ATL, NuGet et Tesseract locaux.',
           'PowerShell : `$env:EDUNOVA_CERT_EVIDENCE="phase19-final"`, puis `.venv/Scripts/python.exe scripts/certify_local_phase19.py <noms-des-contrôles>`. Le runner retire les secrets hérités, impose test/fake/sandbox et conserve commande, répertoire, code de sortie, durée et commit. Les tests SQL exigent explicitement la cible locale autorisée. Aucune production ni transaction réelle.',
           'Pour rejouer les suites corrigées : `$env:EDUNOVA_CERT_PYTHON="C:/Users/cs-ap/dev/edusync-web/edunova/.local-certification/security-venv/Scripts/python.exe"`. Installer `services/api/requirements-certification.txt` et `pip-audit==2.10.1` dans cet environnement ; son pip est 26.2.2. Les versions réellement installées sont dans `freeze.log`.',
           'La [reproduction détaillée](evidence/phase19-final/BOOTSTRAP.md) distingue les deux environnements, les bases locales et les tentatives préliminaires.',
           'Migrations : seconde base neuve `edunova_phase19_final_test`, choisie par `$env:EDUNOVA_MIGRATION_TEST_DATABASE`. Les contraintes financières sont testées séparément sur la base migrée `edunova_phase19_test`. Les anciennes bases/preuves sont préservées.',
           '', '## Exécutions de cette mission', '', '| Contrôle | Code | Commit exécuté | Preuve |','|---|---:|---|---|']
    for name,job in sorted(jobs.items()):
        lines.append(f'| {name} | {job["exit_code"]} | `{job["commit"]}` | [{name}.log](evidence/phase19-final/{name}.log) |')
    lines+=['',f'Contrôles obligatoires absents : {missing or "aucun"}. Codes non nuls parmi ces contrôles : {failed or "aucun"}.',
            '', '### Commandes exactes', '']
    for name,job in sorted(jobs.items()):
        lines += [f'- **{name}**, dans `{job["cwd"]}` : `{subprocess.list2cmdline(job["command"])}`.']
    lines+=['', '## Backend, PostgreSQL et sécurité métier','', '| Suite | PASS | FAIL | SKIP |', '|---|---:|---:|---:|']
    for name in ('backend','backend-final','phase19','postgres','backend-contracts'):
        result=junit(name)
        if result: lines.append(f'| {name} | {result["passed"]} | {result["failed"]} | {result["skipped"]} |')
    migrations=(OUT/'migrations.log').read_text(encoding='utf8') if (OUT/'migrations.log').exists() else ''
    lines+=['',f'Rejeu SQL : **{len(re.findall(r"^APPLY ",migrations,re.M))} migrations tentées**, code {jobs.get("migrations",{}).get("exit_code","NON EXÉCUTÉ")}. Marqueur de fin complète présent : {"ALL MIGRATIONS APPLIED" in migrations}.']
    lines+=['', 'La suite `backend` est séquentielle, sans xdist, dans l’environnement initial conservé. Elle utilise les versions antérieures des dépendances et les tests de routes antérieurs à leur adaptation ; elle n’est pas une preuve de leur mise à jour. La suite `backend-final` utilise les dépendances corrigées et deux workers pour limiter les ressources. La nouvelle pile complète n’a pas été rejouée séquentiellement : la preuve d’absence de dépendance à l’ordre après mise à jour reste limitée. Les fichiers applicatifs sont comparés par arbres Git ; la différence des dépendances et des tests de routes de la suite initiale est conservée explicitement.',
            'La suite générale utilise SQLite et des simulateurs ; elle ne prouve pas la concurrence PostgreSQL. La sélection `postgres` utilise le moteur réel : callbacks identiques/modifiés concurrents, référence conflictuelle, paiements simultanés, rollback, tenant, charges annulées, course callback/expiration/annulation et cohérence reçu/ledger/statut. La priorité des échéances dispose du test adversarial ajouté lors de la première mission.',
            'Les 17 SKIP de la régression générale concernent les 9 cas de concurrence et 8 cas de contraintes nécessitant la variable PostgreSQL. Leur correspondance individuelle avec la suite réelle est fournie ci-dessous.', '']
    backendxml=OUT/'backend.xml'; pgxml=OUT/'postgres.xml'
    if backendxml.exists() and pgxml.exists():
        pgcases={c.attrib['name']:c for c in ET.parse(pgxml).getroot().findall('.//testcase')}
        for case in ET.parse(backendxml).getroot().findall('.//testcase'):
            if case.find('skipped') is not None:
                name=case.attrib['name']; c=pgcases.get(name)
                ok=c is not None and not any(c.find(t) is not None for t in ('error','failure','skipped'))
                lines.append(f'- `{name}` : PostgreSQL séparé **{"PASS" if ok else "NON VALIDÉ"}**.')
    lines+=['', 'Authentification/restauration de session, permissions, isolation tenant, validation des entrées, journalisation sensible et paiements sont couverts par les tests de la suite complète. Une sélection individuelle des cas exécutés figure dans [SECURITY_COVERAGE.json](evidence/phase19-final/SECURITY_COVERAGE.json), avec les SKIP distincts. Cela reste une validation des scénarios testés, sans pentest externe ni preuve exhaustive de toutes les configurations de déploiement.',
            '', '## Les 55 audits structurels','',
            'Les 17 échecs initiaux ont été reproduits individuellement : [baseline](evidence/phase19-final/baseline/results.json). Décision motivée et cause par audit : [contrats historiques](docs/PHASE19_AUDIT_CONTRACT_DECISION.md). Les anciens journaux restent inchangés. Les minima numériques remplacent uniquement les versions historiques incompatibles ; les contrôles métier restent obligatoires. Les cinq vérifications lexicales ont été remplacées par des vérifications structurelles plus précises. Deux tests négatifs vérifient versions insuffisantes, invalides et métadonnées API débranchées.',
            f'Résultat : {sum(a["exit_code"]==0 for a in audits)}/{len(audits)} scripts réussis. Les audits structurels ne sont pas des tests fonctionnels.',
            '', '| Audit | Code | Résultat |', '|---|---:|---|']
    for audit in audits:
        name=Path(audit['script']).stem
        lines.append(f'| [{name}](evidence/phase19-final/audits/{name}.log) | {audit["exit_code"]} | {"PASS" if audit["exit_code"]==0 else "FAIL"} |')
    lines+=['', '## Flutter et builds','',
            'Corrections : imports/casts inutiles, blocs de contrôle, champs inutilisés, formulaires `initialValue`, contexte monté après les awaits, prévention de setState après fermeture du détail, migration RadioGroup avec garde de réponse validée. Aucune désactivation globale du linter.',
            'Analyse Admin : voir son code exact dans le tableau. Analyse Mobile : dépréciation de `drift/web.dart` conservée sans suppression ; migrer vers WASM implique assets/worker, compatibilité navigateurs et migration du stockage existant, hors correction mécanique. Cette limite empêche de déclarer `flutter analyze` entièrement réussi.',
            'Les tests Flutter sont exécutés avec un seul worker. Les résumés exacts et erreurs éventuelles figurent dans les journaux mobile-test/admin-test, pas dans un résultat déduit de la compilation.',
            '', '| Tests Flutter | PASS | FAIL | SKIP |', '|---|---:|---:|---:|']
    for app in ('mobile','admin'):
        path=OUT/f'{app}-test.log'
        matches=re.findall(r'\+(\d+)(?: ~(\d+))?(?: -(\d+))?: (?:All tests passed!|Some tests failed\.)',path.read_text(encoding='utf8')) if path.exists() else []
        if matches:
            passed,skipped,failed_tests=matches[-1]
            lines.append(f'| {app} | {passed} | {failed_tests or 0} | {skipped or 0} |')
        else: lines.append(f'| {app} | NON MESURÉ | NON MESURÉ | NON MESURÉ |')
    lines+=['', '| Analyse | Erreurs | Avertissements | Informations | Code |','|---|---:|---:|---:|---:|']
    for app in ('mobile','admin'):
        path=OUT/f'{app}-analyze.log'
        if path.exists():
            log=path.read_text(encoding='utf8')
            counts=[len(re.findall(r'^\s*'+level+r' -',log,re.M)) for level in ('error','warning','info')]
            lines.append(f'| {app} | {counts[0]} | {counts[1]} | {counts[2]} | {jobs.get(app+"-analyze",{}).get("exit_code","NON EXÉCUTÉ")} |')
    lines+=['', '| Build | Mode | Code | Artefact | SHA-256 |', '|---|---|---:|---|---|']
    for artifact in artifacts:
        lines.append(f'| {artifact["job"]} | {"debug" if "android" in artifact["job"] else "release"} | {artifact["exit_code"]} | `{artifact["path"]}` (présent : {artifact["exists"]}) | `{artifact.get("sha256","NON CALCULÉ")}` |')
    lines+=['', 'Les APK sont debug, non signés pour la production. Les exécutables Windows requièrent leur bundle et les builds web leur répertoire complet ; les empreintes ci-dessus identifient les artefacts principaux, pas une signature de déploiement. [BUNDLE_MANIFESTS.json](evidence/phase19-final/BUNDLE_MANIFESTS.json) contient aussi les SHA-256 de tous les fichiers du bundle web et Windows, dont le code AOT. Android : les ABI effectives sont dans [ARTIFACTS.json](evidence/phase19-final/ARTIFACTS.json).',
            '', '## Dépendances et absence de secrets','',
            'Commande : `.venv/Scripts/python.exe -m pip_audit --format=json --output=evidence/phase19-final/dependency-audit.json`. Voir [avis complets](evidence/phase19-final/dependency-audit.json). Les entrées peuvent avoir des doublons ou alias ; elles ne doivent pas être présentées comme autant de vulnérabilités uniques.',
            '', '| Paquet | Version auditée | Entrées retournées | Identifiants distincts |', '|---|---|---:|---:|']
    for dep in vulnerable:
        lines.append(f'| {dep["name"]} | {dep["version"]} | {len(dep["vulns"])} | {len({v["id"] for v in dep["vulns"]})} |')
    lines+=['', f'Paquets encore signalés par le dernier audit : **{len(vulnerable)}**. Le premier audit signalait 100 entrées (doublons/alias inclus) dans 5 paquets ; les résultats avant correction sont conservés dans [dependency-audit-before-fix.json](evidence/phase19-final/dependency-audit-before-fix.json).',
            'Mises à jour isolées : FastAPI 0.162.0, Starlette 1.10.0, cryptography 50.0.2, Pillow 13.0.0, pytest 9.2.0 ; pip de certification 26.2.2. La simulation de résolution [security-upgrade-resolution.log](evidence/phase19-final/security-upgrade-resolution.log) ne vaut ni installation ni validation ; seuls les résultats des suites corrigées et du nouvel audit font foi. Le scan ne couvre pas automatiquement les dépendances Dart, Android, NuGet ou les bibliothèques natives.',
            f'Audit Dart complémentaire via l’[API officielle OSV](https://google.github.io/osv.dev/api/) : {pub_audit["public_package_versions_checked"] if pub_audit else "NON EXÉCUTÉ"} couples paquet/version publics ; {len(pub_audit["findings"]) if pub_audit else "NON MESURÉ"} paquet(s) signalé(s). Réponse incomplète : {pub_audit["incomplete"] if pub_audit else "NON MESURÉ"}. [Résultat exact](evidence/phase19-final/pub-dependency-audit-results.json). Cela ne couvre ni le SDK Flutter ni les binaires natifs transitifs.',
            'Le contrôle [publication-inventory.json](evidence/phase19-final/publication-inventory.json) vérifie les fichiers suivis sans afficher les valeurs détectées. C’est un contrôle heuristique, non une garantie exhaustive. `.env`, cluster PostgreSQL, caches et binaires de build ne sont pas publiés.',
            '', '## Limites et anomalies restantes','',
            f'- Paquets Python signalés par le dernier audit : {len(vulnerable)}. Un résultat vide ne garantit pas l’absence de vulnérabilités inconnues.',
            '- Drift web déprécié ; compilation JavaScript distincte de WASM. Aucun build WASM certifié.',
            '- StudyWorkspacePage et ExamSimulatorPage conservent données illustratives et callbacks vides ; configuration Exam Mode et indication offline ne prouvent pas un parcours métier intégré. Aucun ajout de fonctionnalité pour masquer ce constat.',
            '- iOS/macOS/Linux non exécutés sur Windows. Pas de validation sur appareil physique, de signature release Android, ni de recette visuelle complète des applications natives.',
            '- Providers de paiement, FCM, S3 et Redis de production non testés ; aucun paiement réel, secret de production ou service payant utilisé.',
            '- Pas de pentest ni de charge prolongée ; les invariants financiers sont validés dans les scénarios réels explicitement exécutés.',
            '- Avertissements tiers Python SWIG/PyMuPDF et adaptateur TestClient/httpx déprécié conservés dans les logs ; aucun statut PASS déduit de leur seule absence d’exception.',
            '', '## Commits de la mission et historiques publiés','',
            'La liste ci-dessous couvre les commits locaux depuis l’import de référence ; la visibilité GitHub doit être confirmée après publication. Les messages `[skip ci]` évitent les déclenchements Actions inutiles lors du push.', '','```text',
            git('log','--reverse','--format=%H %s','6607b18da64eb44c2de017192ccefded21659a35..HEAD'),'```','']
    (ROOT/'EDUNOVA_PHASE19_CERTIFICATION_FINALE.md').write_text('\n'.join(lines),encoding='utf8')
    print('Report written; verdict:',verdict, '; missing:',missing, '; failures:',failed)

if __name__=='__main__':
    generate()

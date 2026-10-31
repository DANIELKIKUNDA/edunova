"""Build a verifiable report from recorded commands, logs and JUnit files."""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
out = root / 'evidence/local-phase19'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
def read(name):
    p = out / name
    return p.read_text(encoding='utf-8', errors='replace') if p.exists() else ''
def meta(name):
    return json.loads(read(name+'.json')) if read(name+'.json') else {}
def junit(name):
    p = out / (name+'.xml')
    if not p.exists(): return 'NON TERMINÉ / aucun JUnit final'
    cases = list(ET.parse(p).getroot().iter('testcase'))
    failed = sum(c.find('failure') is not None or c.find('error') is not None for c in cases)
    skipped = sum(c.find('skipped') is not None for c in cases)
    return f'{len(cases)-failed-skipped} réussis, {failed} échecs/erreurs, {skipped} ignorés'
def flutter(name):
    if not meta(name): return 'NON TERMINÉ : aucun code de sortie final'
    if meta(name).get('exit_code') == 124: return 'Interrompu à la limite de temps ; aucun PASS de suite'
    matches = re.findall(r'\d\d:\d\d \+(\d+)(?: ~(\d+))?(?: -(\d+))?: (?:All tests passed!|Some tests failed\.)', read(name+'.log'))
    if not matches: return 'Non conclu : voir journal et code de sortie'
    passed, skipped, failed = matches[-1]
    return f'{passed} réussis, {failed or 0} échecs, {skipped or 0} ignorés'
def analysis(name):
    lines = read(name+'.log').splitlines()
    return ', '.join(f'{sum(bool(re.match(pattern, line)) for line in lines)} {label}' for pattern,label in [(r'\s*error -','erreurs'),(r'\s*warning -','avertissements'),(r'\s*info -','informations')])
def cause(message):
    if 'tesseract binary' in message: return 'Binaire OCR absent du PATH. Correctif : Tesseract isolé et modèles eng/fra, PATH limité au runner.'
    if 'Permission denied' in message: return 'Réouverture Windows d’un NamedTemporaryFile encore ouvert. Correctif : TemporaryDirectory et fermeture du writer avant le pipeline.'
    if 'cannot open resource' in message: return 'Police de test Linux absente sous Windows. Correctif : police Windows ou repli redimensionné Pillow.'
    if "'open' == 'paid'" in message: return 'Allocation atomique par identifiant plutôt que par échéance. Correctif : ordre des verrous conservé, allocation triée par échéance.'
    if 'expired' in message or 'cancelled' in message: return 'Écriture terminale obsolète après callback. Correctif : revérification sous verrou avant sauvegarde.'
    if 'outcomes' in message: return 'Cause probable : pollution de contexte/limitation dans la suite séquentielle. Reproduire isolément ; la régression finale complète doit être consultée séparément.'
    if 'claimed' in message: return 'Cause probable : autres jobs laissés en file par les échecs précédents. Isoler la file du test et rejouer après correction de l’ingestion.'
    return 'Voir trace. Reproduire le cas isolément et réconcilier le contrat avant de modifier les assertions.'

# Full individual traces remain in JUnit; the appendix gives a command, cause and
# proposed/applied correction for each recorded failure, including earlier runs.
appendix = ['# Annexe des échecs et corrections', '', 'Les traces complètes sont conservées dans les XML et journaux cités. Les anciennes tentatives ne sont pas des échecs résiduels si une reprise correspondante a réussi.', '']
for p in sorted(out.glob('*.xml')):
    for case in ET.parse(p).getroot().iter('testcase'):
        node = case.find('failure')
        if node is None: node = case.find('error')
        if node is None: continue
        casepath = case.get('classname','').replace('.', '/') + '.py::' + case.get('name','')
        message = node.get('message','')
        appendix += [f"## {p.stem} — {case.get('name')}", '', f"Commande de reproduction : `.venv/Scripts/python.exe -m pytest -q '{casepath}'`.", '', cause(message), '', f'Trace complète : [{p.name}]({p.name}).', '', '```text', (node.text or message)[:3500], '```', '']
for name in ('mobile-test','admin-test'):
    lines = read(name+'.log').splitlines()
    for i,line in enumerate(lines):
        if not re.match(r'^\d\d:\d\d .*\[E\]',line): continue
        appendix += [f'## Flutter — {line}', '', f'Commande : `flutter test --no-pub --reporter=expanded` dans `apps/{name.split("-")[0]}`.', '', 'Cause probable et correction proposée : vérifier les fixtures de session, la portée Riverpod, les réponses simulées et le ciblage du widget. Ne pas désactiver les assertions de confidentialité.', '', f'Trace complète : [{name}.log]({name}.log). Extrait du flux de test :', '', '```text', '\n'.join(lines[max(0,i-45):i+5]), '```', '']
auditpath = out / 'audits/results.json'
audits = json.loads(auditpath.read_text()) if auditpath.exists() else []
for item in audits:
    if item['exit_code'] == 0: continue
    log = out / 'audits' / (Path(item['script']).stem+'.log')
    appendix += [f"## Audit structurel — {item['script']}", '', f"Commande : `.venv/Scripts/python.exe -X utf8 {item['script']}` ; sortie {item['exit_code']}.", '', 'Cause à réconcilier : assertion structurelle historique, fichier attendu ou contrat de version. Correctif proposé : comparer chaque assertion au contrat actuel puis corriger le code ou actualiser le contrôle sans affaiblir ses garanties. Non corrigé et non assimilé à un test fonctionnel PASS.', '', '```text', '\n'.join(log.read_text(encoding='utf-8',errors='replace').splitlines()[-25:]), '```', '']
(out/'FAILURES.md').write_text('\n'.join(appendix), encoding='utf-8')

records = []
for p in sorted(out.glob('*.json')):
    value = json.loads(p.read_text(encoding='utf-8'))
    if isinstance(value,dict) and 'command' in value:
        records.append((p.stem,value))
commands = ['# Commandes exécutées', '', 'Chaque ligne correspond à une tentative réelle. Un code zéro d’audit structurel ou de collecte ne signifie pas que les tests fonctionnels ont été exécutés.', '', '| Tentative | Commit enregistré au lancement | Sortie | Durée s | Commande |', '|---|---|---:|---:|---|']
for name, item in records:
    commands.append(f"| [{name}]({name}.log) | `{item.get('commit','non enregistré ; tentative initiale avant instrumentation')}` | {item['exit_code']} | {item['seconds']} | `{subprocess.list2cmdline(item['command'])}` |")
    if item['exit_code'] == 0: continue
    logtext = read(name+'.log')
    if 'android' in name:
        explanation = 'Build Android non certifié pour cette tentative. Examiner le téléchargement SDK/NDK, les erreurs Google Maven et le daemon Gradle ; reprendre séquentiellement après vérification réseau et avec une mémoire compatible avec les 6 Go de la machine. Aucun APK ne doit être déclaré valide sans sortie zéro et artefact vérifié.'
    elif 'windows' in name:
        explanation = 'Vérifier successivement le support des symlinks, NuGet, ATL et le préfixe CMake. Ces prérequis/caches ont été corrigés au fil des reprises. Un exécutable intermédiaire ne prouve pas que le bundle INSTALL a réussi.'
    elif 'analyze' in name:
        explanation = 'Les erreurs de syntaxe/import/API ont été corrigées puis réanalysées. Si seules des informations et avertissements restent, le code de sortie standard reste non nul : effectuer une remise à niveau des dépréciations/lints sans désactiver les contrôles.'
    elif 'test' in name:
        explanation = 'Voir les cas et traces du journal : anciens imports/API, fixtures incomplètes, session asynchrone, portée Riverpod ou délai de chargement. Les reprises séquentielles conservent les assertions de sécurité.'
    else:
        explanation = 'Consulter les cas individuels et les corrections décrites dans le rapport ; les suites et audits historiques restent distincts.'
    excerpt = logtext if len(logtext)<4500 else logtext[:1000]+'\n[extrait ; trace intégrale dans le journal]\n'+logtext[-3000:]
    appendix += [f'## Tentative non réussie — {name}', '', f"Commande : `{subprocess.list2cmdline(item['command'])}` dans `{item['cwd']}`. Code {item['exit_code']}.", '', explanation, '', f'Trace intégrale : [{name}.log]({name}.log).', '', '```text', excerpt, '```', '']
(out/'FAILURES.md').write_text('\n'.join(appendix), encoding='utf-8')
(out/'COMMANDS.md').write_text('\n'.join(commands), encoding='utf-8')
for app in ('mobile','admin'):
    lock = root / 'apps' / app / 'pubspec.lock'
    if lock.exists(): shutil.copyfile(lock,out/(app+'-dependencies.lock'))
verbose = out/'mobile-pub-verbose.log'
if verbose.exists():
    lines = verbose.read_text(encoding='utf-8',errors='replace').splitlines()
    (out/'mobile-pub-network-summary.log').write_text('\n'.join(line for line in lines if len(line)<1500 and line.startswith(('IO  : HTTP','MSG :','ERR :'))),encoding='utf-8')

jobs = ['compile','pip-check','migrations','backend-final','backend-contracts','phase19','postgres','audits','mobile-pub','mobile-codegen','mobile-analyze','mobile-test','mobile-web','mobile-windows','mobile-android','admin-pub','admin-analyze','admin-test','admin-web','admin-windows','admin-android']
table = ['| Contrôle | Résultat mesuré | Code | Commit de la tentative | Preuve |','|---|---|---:|---|---|']
for name in jobs:
    item = meta(name)
    result = junit(name) if name in ('backend-final','backend-contracts','phase19','postgres') else flutter(name) if name.endswith('-test') else analysis(name) if name.endswith('-analyze') else 'Terminé' if item.get('exit_code')==0 else 'ÉCHEC' if item else 'NON TERMINÉ'
    table.append(f"| {name} | {result} | {item.get('exit_code','—')} | `{item.get('commit','non enregistré')}` | [{name}.log](evidence/local-phase19/{name}.log) |")
pending = [name for name in jobs if not meta(name)]
completion = ('PROVISOIRE : restent sans sortie finale : ' + ', '.join(pending)) if pending else 'Bilan terminé pour les commandes listées ; les échecs et limites ci-dessous restent explicites.'
history = subprocess.check_output(['git','log','--format=%H %s','6607b18..HEAD'],cwd=root,text=True)
skipped_rows = []
backend_xml = out/'backend-final.xml'
if backend_xml.exists():
    for case in ET.parse(backend_xml).getroot().iter('testcase'):
        skipped = case.find('skipped')
        if skipped is not None:
            skipped_rows.append(f"- `{case.get('classname')}::{case.get('name')}` : {skipped.get('message','raison dans JUnit')}.")
artifact_rows = []
for job, relative in [('mobile-web','apps/mobile/build/web/main.dart.js'),('admin-web','apps/admin/build/web/main.dart.js'),('mobile-windows','apps/mobile/build/windows/x64/runner/Release/edunova.exe'),('admin-windows','apps/admin/build/windows/x64/runner/Release/edunova_admin.exe'),('mobile-android','apps/mobile/build/app/outputs/flutter-apk/app-debug.apk'),('admin-android','apps/admin/build/app/outputs/flutter-apk/app-debug.apk')]:
    path = root/relative
    if meta(job).get('exit_code') == 0:
        artifact_rows.append({'job':job,'path':relative,'exists':path.exists(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None})
(out/'ARTIFACTS.json').write_text(json.dumps(artifact_rows,indent=2),encoding='utf-8')
artifact_text = '\n'.join(f"- `{a['path']}` : SHA-256 `{a['sha256']}` ; présence vérifiée : {a['exists']}." for a in artifact_rows)
text = f'''# EduNova — certification locale jusqu’à la Phase 19

Rapport généré le {datetime.now(ZoneInfo('Africa/Lubumbashi')).isoformat(timespec='seconds')}.

## Verdict : PARTIELLEMENT CERTIFIÉ

Les réussites ci-dessous sont limitées aux contrôles effectivement exécutés. Elles ne clôturent pas automatiquement les Phases 1–19. Les avertissements d’analyse, audits structurels en échec et éventuels builds bloqués restent des réserves.

{completion}

## Dépôt et commits

- Dépôt : DANIELKIKUNDA/edunova ; branche import/edunova-v0.57.12.
- Import initial propre : `6607b18da64eb44c2de017192ccefded21659a35`.
- HEAD source lors de la génération : `{head}`. Les commits exacts de chaque suite sont inscrits dans le tableau et les JSON. Les contrôles couvrent plusieurs commits successifs ; ne pas attribuer tous les anciens résultats à HEAD.
- PR #1 vérifiée ouverte, non fusionnée et en brouillon. Aucun changement demandé à main.
- Les corrections sont des commits locaux non poussés ; la PR distante est restée sur le commit d’import au dernier contrôle. Ne pas chercher les nouveaux commits sur GitHub avant leur publication explicite.
- Dossier local : `C:/Users/cs-ap/dev/edusync-web/edunova`. Le dépôt parent edusync-web et ses modifications locales sont conservés.

## Environnement

Windows 11 x64 ; Git 2.51.0.windows.1 ; Python 3.13.14 dans `.venv` ; pytest 9.0.2 ; pytest-xdist 3.8.0 ; PostgreSQL 16.11 ; Flutter 3.35.4 ; Dart 3.9.2 ; Android SDK 36 / Java 21 ; Visual Studio Community 2022 17.14.41. Voir `flutter-doctor.log` pour les détails.

Tesseract 5.5.3.20260724 installé dans `.local-certification/tesseract`, avec eng/fra. Source Windows vérifiée : [documentation UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). NuGet 6.14.0 est téléchargé localement pour flutter_tts. Le composant C++ ATL a été installé et les en-têtes `atlstr.h` vérifiés sur disque ; `atl-install-exit.txt` et `atl-install-verification.txt` conservent la sortie de l’installeur et la confirmation.

Les SDK étaient absents du PATH initial mais présents sur disque. Docker client est installé ; le moteur Docker n’était pas disponible, il n’a pas servi de preuve. Le mode Développeur Windows a ensuite été activé par l’utilisateur.

## Configuration et dépendances

Le clone ne contenait pas de `.env`. Les noms des variables du modèle ont été vérifiés sans afficher de secrets. Le runner retire les variables sensibles héritées, impose le mode test et n’utilise pas de prestataire de paiement réel. Les dépendances Python déclarées ont été installées ; `freeze.log` conserve les versions résolues et `pip-check.log` leur cohérence. Les résolutions Flutter sont conservées dans les fichiers `*-dependencies.lock`. Aucune opération financière réelle ni aucun service payant n’a été utilisé.

## Résultats et commandes

Les nombres des suites se recouvrent : ne pas les additionner comme des tests uniques. La collecte seule et les audits structurels ne sont pas des suites fonctionnelles.

{chr(10).join(table)}

Inventaire exhaustif des tentatives instrumentées : [COMMANDS.md](evidence/local-phase19/COMMANDS.md). Toutes les reprises sont archivées sous `*-previous-*`. Les tentatives initiales de lancement, clonage et installation sont décrites ci-dessous et dans les journaux racine d’evidence.

## PostgreSQL et finance

Cluster dédié créé par `initdb -D .local-certification/postgres -U edunova_cert --auth=trust --encoding=UTF8 --locale=C`, limité à `127.0.0.1:55439`. Base : `edunova_phase19_test`. Aucune connexion aux bases existantes ou de production. Les 99 migrations 0001–0099 ont été appliquées via `psql -X -v ON_ERROR_STOP=1` ; preuve `migrations.log`.

La régression générale utilise SQLite isolé par processus. Les suites financières PostgreSQL utilisent une variable distincte, validée contre l’adresse/port/base dédiés et un schéma UUID par test ; leurs tables proviennent de SQLAlchemy. Les huit contrôles de contraintes, séparément, interrogent le schéma public réellement migré et testent les rejets d’écritures invalides. Ce découpage ne constitue pas une validation de tout le backend sur PostgreSQL.

Contrôles financiers exécutés : callback identique simultané à quatre transactions ; payload modifié rejeté ; paiements distincts simultanés sans perte d’allocation ; référence externe conflictuelle ; référence fournisseur conflictuelle avec rollback du second intent ; rollback sur erreur d’insertion de grand livre et de mise à jour des frais ; rejet inter-universités ; frais annulés ; reçu inversé ; expiration/annulation avant callback et état obsolète après callback ; cohérence reçu/grand livre/statut ; allocation suivant les échéances et non l’ordre des UUID. Voir les JUnit et les tests `test_phase19_*`.

Deux défauts critiques ont été reproduits avant correction : expiration/annulation obsolète écrasant succeeded après comptabilisation, et allocation des frais selon l’ordre des identifiants. Les traces antérieures sont conservées ; la réussite d’une reprise ne supprime pas cette histoire.

## Corrections réalisées

Isolation du fichier SQLite par processus Windows ; mode PostgreSQL de test explicitement limité à la base dédiée ; verrous de transitions terminales ; ordre d’allocation par échéance ; fermeture des fichiers temporaires avant réouverture OCR ; polices de tests portables ; imports Dart manquants ; erreurs de parenthèses ; API notifications 20 et contrainte de version cohérente ; gestion des paramètres Dio ; icônes disponibles ; génération Drift et hôtes web/Windows/Android. Les importants fichiers générés sont identifiés comme tels, sans refonte du domaine.

Les fixtures Flutter ont été adaptées aux interfaces réelles : portée Riverpod et données locales contrôlées, stockage sécurisé simulé, attente de restauration de session, faux dépôts de synchronisation complets, ciblage de la liste défilante. Les assertions de refus inter-tenant, de non-écriture partielle et de masquage sont conservées. Le test d’intervalle easy attend 33 : 10 × 2,5 × 1,3 = 32,5, arrondi Dart existant ; l’algorithme métier n’a pas été modifié pour ce test.

La machine dispose d’environ 6 Go de RAM. Après une tentative de tests interrompue au chargement, le runner Flutter utilise un seul worker ; Gradle est limité à 2 Go et deux workers. Le préfixe CMake par défaut resté en cache après une configuration interrompue est réparé pour installer le bundle dans le dossier de build, sans écrire dans Program Files. Ces modifications sont des corrections de configuration, pas une suppression de tests.

## Artefacts effectivement vérifiés

{artifact_text}

La présence et l’empreinte d’un artefact ne certifient ni son lancement sur appareil ni ses services distants. Les fichiers intermédiaires d’un build échoué sont exclus de cette liste.

## Anomalies, traces et correctifs proposés

[FAILURES.md](evidence/local-phase19/FAILURES.md) fait partie de ce rapport : commande, trace, cause probable et correction appliquée/proposée pour chaque échec pytest, Flutter résiduel et audit historique. Les traces complètes restent dans les XML/logs. Les échecs structurels ne sont ni masqués ni convertis en PASS. Leur actualisation doit être précédée d’une revue du contrat concerné.

Les analyses Flutter standard restent non réussies si leur code de sortie vaut 1, même avec zéro erreur compilateur : les avertissements et informations ne sont pas supprimés. Les builds web JavaScript n’attestent pas de la compatibilité Wasm ; les avertissements de dry-run Wasm restent des réserves.

## Non exécuté et limites

Pas de build iOS/macOS sur Windows ; pas de build Linux dans cet environnement. Pas de certification sur appareils physiques, notifications FCM réelles, prestataires financiers réels, charge longue durée, réseau distribué, Redis/S3 réels ou PostgreSQL de production. Aucun paiement réel n’a été déclenché. Les APK demandés sont des builds debug locaux, pas des releases signées de production. Les identifiants Android générés com.example doivent être remplacés et validés avant diffusion.

Les tests ignorés dans la suite générale sont explicitement visibles dans JUnit ; les tests PostgreSQL opt-in ont leur exécution dédiée. Les échecs initiaux dus au réseau sandbox ont été repris après autorisation. La tentative complémentaire offline admin initialement refusée n’a pas été exécutée ; une nouvelle résolution online a été autorisée après la demande de poursuite de l’utilisateur.

{chr(10).join(skipped_rows)}

## Commits de travail

```text
{history}```

Les preuves et ce rapport peuvent être ajoutés dans un commit documentaire ultérieur. Vérifier `git status`, la liste des commits locaux et leur présence distante avant toute reprise. Aucune fusion dans main n’est effectuée.
'''
(root/'EDUNOVA_CERTIFICATION_LOCALE_PHASE19.md').write_text(text,encoding='utf-8')
print('Report written for',head)

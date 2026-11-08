# Reproduction Windows de cette seconde mission

Les commandes sont exécutées depuis `C:/Users/cs-ap/dev/edusync-web/edunova`.
EduSync parent n'est pas modifié. Les SDK et le cluster initial ont été préparés
lors de la première mission ; voir `../local-phase19/BOOTSTRAP.md` et son rapport.
Les dossiers `.local-certification`, `.venv` et les builds restent ignorés par Git.

## Séparation des environnements Python

L'environnement `.venv` initial a été conservé sans remplacement de ses versions
applicatives. Sa régression séquentielle est enregistrée sous `backend` ; elle
précède l'adaptation des deux fichiers de tests d'introspection de routes.

```powershell
.\.venv\Scripts\python.exe -m venv .local-certification/security-venv
& '.\.local-certification\security-venv\Scripts\python.exe' -m pip install --upgrade 'pip==26.2.2'
& '.\.local-certification\security-venv\Scripts\python.exe' -m pip install -r services/api/requirements-certification.txt 'pip-audit==2.10.1'
$env:EDUNOVA_CERT_EVIDENCE='phase19-final'
$env:EDUNOVA_CERT_PYTHON=(Resolve-Path '.local-certification/security-venv/Scripts/python.exe').Path
$env:EDUNOVA_CERT_WORKERS='2'
& $env:EDUNOVA_CERT_PYTHON scripts/certify_local_phase19.py pip-check freeze security-audit backend-final
& $env:EDUNOVA_CERT_PYTHON scripts/certify_local_phase19.py backend-contracts phase19 postgres audits
```

Les fichiers `security-pip-bootstrap.log`, `security-environment-install.log` et
`freeze.log` conservent les versions installées. Le premier `pip_audit`, dans
`.venv`, a échoué avec 100 entrées (doublons et alias inclus). Son JSON et son log
sont sauvegardés avec le suffixe `before-fix`. La résolution `pip install
--dry-run --report ...` est conservée séparément ; elle n'est pas un test PASS.

## PostgreSQL uniquement local

Le cluster dédié existe dans `.local-certification/postgres`, configuré pour
`127.0.0.1:55439`, compte `edunova_cert`. Aucune base de production n'est utilisée.

```powershell
& 'C:/Program Files/PostgreSQL/16/bin/pg_ctl.exe' -D .local-certification/postgres -l .local-certification/postgres-final-server.log -o '-c config_file=C:/Users/cs-ap/dev/edusync-web/edunova/.local-certification/server.conf' start
& 'C:/Program Files/PostgreSQL/16/bin/createdb.exe' -h 127.0.0.1 -p 55439 -U edunova_cert edunova_phase19_final_test
$env:EDUNOVA_MIGRATION_TEST_DATABASE='edunova_phase19_final_test'
& $env:EDUNOVA_CERT_PYTHON scripts/certify_local_phase19.py migrations
```

La création suppose une base finale encore absente ; ne pas supprimer une base
existante pour reproduire ce rapport. Les contraintes sont vérifiées sur la base
isolée `edunova_phase19_test` contenant les mêmes 99 migrations. Les fixtures de
concurrence utilisent des schémas UUID indépendants, puis les retirent. Les tests
de contraintes effectuent un rollback après chaque cas. Le runner fixe lui-même
le DSN PostgreSQL et la fixture refuse toute autre cible.

## Flutter et preuves

```powershell
.\.venv\Scripts\python.exe scripts/certify_local_phase19.py mobile-pub admin-pub mobile-analyze admin-analyze mobile-test admin-test mobile-web admin-web mobile-windows admin-windows mobile-android admin-android
```

Après correction du débordement workspace, les analyses et suites ont été
relancées, puis les trois builds Mobile reconstruits. Admin conserve ses builds
précédents avec code applicatif identique, vérifié par arbre Git. Les tests
widget nouveaux ont demandé une seconde exécution. Les reprises archivées ne
sont pas supprimées. Le fichier `workspace-targeted.log` est une reproduction
du débordement **avant** correction, pas le résultat final.

La première exécution modifiée des audits a accidentellement compté le helper
`audit_contracts.py` comme un 56e script, sans contrôle métier. Le helper a été
renommé `historical_audit_contracts.py` avant stabilisation. Seules les reprises
versionnées à 55 scripts font foi. Les logs préliminaires sont conservés ; ils
ne constituent pas une exécution sur arbre propre du commit initial affiché.

## Publication

`scripts/certify_publication_inventory.py` examine les fichiers suivis et les
blobs ajoutés depuis l'import, sans imprimer les valeurs détectées. Ce contrôle
heuristique n'est pas une garantie exhaustive d'absence de secrets. Les preuves
n'incluent pas les APK, DLL, exécutables, cluster, `.env` ou caches téléchargés.
Les manifests enregistrent leurs empreintes locales.

Le connecteur GitHub a renvoyé « Transport closed ». Le script de livraison
utilise l'API officielle avec le credential Git déjà disponible, tenu uniquement
en mémoire. Il conserve la description existante de la PR, ajoute une section
balisée et refuse de modifier une PR hors du périmètre brouillon/main attendu.
Le push est normal, sans force ; le dernier commit porte `[skip ci]`.

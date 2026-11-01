# EduNova — certification finale de la Phase 19

Généré le 2026-11-01T22:13:40.246977+02:00.

## Verdict : PARTIELLEMENT CERTIFIÉ

Cette certification locale n’autorise pas une mise en production. Les constats sont issus des exécutions conservées ; aucune réussite n’est déduite d’un ancien build.

## Livraison et provenance

HEAD de préparation du rapport : `08d1143736ba014e0822454675d6b9ea3a5d2bd4`. Les commits documentaires de livraison peuvent lui succéder ; le SHA final publié est consigné dans la conversation PR #1 et dans le bilan de livraison.
Branche : `import/edunova-v0.57.12`. Aucun merge dans main. La publication finale et le statut brouillon doivent être vérifiés après le push ; voir [publication.json](evidence/phase19-final/publication.json).
Les commits testés sont indiqués individuellement ci-dessous. [TREE_IDENTITY.json](evidence/phase19-final/TREE_IDENTITY.json) compare les sources réellement exécutées aux sources livrées, y compris les dépendances déclarées.
Les échecs, commandes, traces et correctifs intermédiaires figurent dans [DIAGNOSTICS.md](evidence/phase19-final/DIAGNOSTICS.md).

## Environnement et reproduction

Windows 11 x64, Git 2.51.0, Python 3.13.14 ; environnement initial `.venv` conservé et environnement corrigé `.local-certification/security-venv` séparé. Flutter 3.35.4 / Dart 3.9.2, PostgreSQL 16.11 local : `127.0.0.1:55439`, utilisateur de test `edunova_cert`. SDK Android local, Java 21, Visual Studio 2022 avec ATL, NuGet et Tesseract locaux.
PowerShell : `$env:EDUNOVA_CERT_EVIDENCE="phase19-final"`, puis `.venv/Scripts/python.exe scripts/certify_local_phase19.py <noms-des-contrôles>`. Le runner retire les secrets hérités, impose test/fake/sandbox et conserve commande, répertoire, code de sortie, durée et commit. Les tests SQL exigent explicitement la cible locale autorisée. Aucune production ni transaction réelle.
Pour rejouer les suites corrigées : `$env:EDUNOVA_CERT_PYTHON="C:/Users/cs-ap/dev/edusync-web/edunova/.local-certification/security-venv/Scripts/python.exe"`. Installer `services/api/requirements-certification.txt` et `pip-audit==2.10.1` dans cet environnement ; son pip est 26.2.2. Les versions réellement installées sont dans `freeze.log`.
Migrations : seconde base neuve `edunova_phase19_final_test`, choisie par `$env:EDUNOVA_MIGRATION_TEST_DATABASE`. Les contraintes financières sont testées séparément sur la base migrée `edunova_phase19_test`. Les anciennes bases/preuves sont préservées.

## Exécutions de cette mission

| Contrôle | Code | Commit exécuté | Preuve |
|---|---:|---|---|
| admin-analyze | 0 | `f92878e7196711cbdbb30eb004f6252a3541eb44` | [admin-analyze.log](evidence/phase19-final/admin-analyze.log) |
| admin-android | 0 | `edb7876cb26c131ec13c15e33f40b98022801e33` | [admin-android.log](evidence/phase19-final/admin-android.log) |
| admin-pub | 0 | `716a11fcb8c98073e218290bdc020ed98ade5886` | [admin-pub.log](evidence/phase19-final/admin-pub.log) |
| admin-test | 0 | `f92878e7196711cbdbb30eb004f6252a3541eb44` | [admin-test.log](evidence/phase19-final/admin-test.log) |
| admin-web | 0 | `b4a8eabafa7d6a1f50f4cc4cc43fc610a1040fbb` | [admin-web.log](evidence/phase19-final/admin-web.log) |
| admin-windows | 0 | `b4a8eabafa7d6a1f50f4cc4cc43fc610a1040fbb` | [admin-windows.log](evidence/phase19-final/admin-windows.log) |
| audit-contract-tests | 0 | `edb7876cb26c131ec13c15e33f40b98022801e33` | [audit-contract-tests.log](evidence/phase19-final/audit-contract-tests.log) |
| audits | 0 | `9424aa1ce5e928aa0e3c5f30daba6ec773c1a509` | [audits.log](evidence/phase19-final/audits.log) |
| backend | 0 | `716a11fcb8c98073e218290bdc020ed98ade5886` | [backend.log](evidence/phase19-final/backend.log) |
| backend-contracts | 0 | `9424aa1ce5e928aa0e3c5f30daba6ec773c1a509` | [backend-contracts.log](evidence/phase19-final/backend-contracts.log) |
| compile | 0 | `716a11fcb8c98073e218290bdc020ed98ade5886` | [compile.log](evidence/phase19-final/compile.log) |
| freeze | 0 | `edb7876cb26c131ec13c15e33f40b98022801e33` | [freeze.log](evidence/phase19-final/freeze.log) |
| migrations | 0 | `b4a8eabafa7d6a1f50f4cc4cc43fc610a1040fbb` | [migrations.log](evidence/phase19-final/migrations.log) |
| mobile-analyze | 1 | `f92878e7196711cbdbb30eb004f6252a3541eb44` | [mobile-analyze.log](evidence/phase19-final/mobile-analyze.log) |
| mobile-android | 0 | `9424aa1ce5e928aa0e3c5f30daba6ec773c1a509` | [mobile-android.log](evidence/phase19-final/mobile-android.log) |
| mobile-pub | 0 | `716a11fcb8c98073e218290bdc020ed98ade5886` | [mobile-pub.log](evidence/phase19-final/mobile-pub.log) |
| mobile-test | 0 | `f92878e7196711cbdbb30eb004f6252a3541eb44` | [mobile-test.log](evidence/phase19-final/mobile-test.log) |
| mobile-web | 0 | `f92878e7196711cbdbb30eb004f6252a3541eb44` | [mobile-web.log](evidence/phase19-final/mobile-web.log) |
| mobile-windows | 0 | `9424aa1ce5e928aa0e3c5f30daba6ec773c1a509` | [mobile-windows.log](evidence/phase19-final/mobile-windows.log) |
| phase19 | 0 | `9424aa1ce5e928aa0e3c5f30daba6ec773c1a509` | [phase19.log](evidence/phase19-final/phase19.log) |
| pip-check | 0 | `edb7876cb26c131ec13c15e33f40b98022801e33` | [pip-check.log](evidence/phase19-final/pip-check.log) |
| postgres | 0 | `9424aa1ce5e928aa0e3c5f30daba6ec773c1a509` | [postgres.log](evidence/phase19-final/postgres.log) |
| pub-dependency-audit | 0 | `339100bad268775b8e055f8f311535539d3b52bf` | [pub-dependency-audit.log](evidence/phase19-final/pub-dependency-audit.log) |
| security-audit | 0 | `edb7876cb26c131ec13c15e33f40b98022801e33` | [security-audit.log](evidence/phase19-final/security-audit.log) |

Contrôles obligatoires absents : ['backend-final']. Codes non nuls parmi ces contrôles : aucun.

### Commandes exactes

- **admin-analyze**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub`.
- **admin-android**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub`.
- **admin-pub**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat pub get`.
- **admin-test**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --concurrency=1 --reporter=expanded`.
- **admin-web**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub`.
- **admin-windows**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\admin` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub`.
- **audit-contract-tests**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe C:\Users\cs-ap\dev\edusync-web\edunova\scripts\test_audit_contracts.py`.
- **audits**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.local-certification\security-venv\Scripts\python.exe C:\Users\cs-ap\dev\edusync-web\edunova\scripts\certify_phase19_audits.py`.
- **backend**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe -m pytest -q services/api/tests --junitxml=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\phase19-final\backend.xml`.
- **backend-contracts**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.local-certification\security-venv\Scripts\python.exe -m pytest -q services/api/tests -k "flutter or frontend or migration_contract" --junitxml=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\phase19-final\backend-contracts.xml`.
- **compile**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe -m compileall -q services/api/app services/api/tests`.
- **freeze**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.local-certification\security-venv\Scripts\python.exe -m pip freeze`.
- **migrations**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.venv\Scripts\python.exe C:\Users\cs-ap\dev\edusync-web\edunova\scripts\certify_phase19_migrations.py`.
- **mobile-analyze**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub`.
- **mobile-android**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build apk --debug --no-pub`.
- **mobile-pub**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat pub get`.
- **mobile-test**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --concurrency=1 --reporter=expanded`.
- **mobile-web**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build web --release --no-pub`.
- **mobile-windows**, dans `C:\Users\cs-ap\dev\edusync-web\edunova\apps\mobile` : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat build windows --release --no-pub`.
- **phase19**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.local-certification\security-venv\Scripts\python.exe -m pytest -q services/api/tests/test_phase19_payment_hardening.py services/api/tests/test_phase19_atomic_finance.py services/api/tests/test_phase19_atomic_callback.py --junitxml=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\phase19-final\phase19.xml`.
- **pip-check**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.local-certification\security-venv\Scripts\python.exe -m pip check`.
- **postgres**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.local-certification\security-venv\Scripts\python.exe -m pytest -q services/api/tests/test_phase19_atomic_finance.py services/api/tests/test_phase19_atomic_callback.py services/api/tests/test_phase19_postgres_concurrency.py services/api/tests/test_phase19_postgres_constraints.py --junitxml=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\phase19-final\postgres.xml`.
- **pub-dependency-audit**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.local-certification\security-venv\Scripts\python.exe C:\Users\cs-ap\dev\edusync-web\edunova\scripts\certify_pub_dependencies.py`.
- **security-audit**, dans `C:\Users\cs-ap\dev\edusync-web\edunova` : `C:\Users\cs-ap\dev\edusync-web\edunova\.local-certification\security-venv\Scripts\python.exe -m pip_audit --format=json --output=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\phase19-final\dependency-audit.json`.

## Backend, PostgreSQL et sécurité métier

| Suite | PASS | FAIL | SKIP |
|---|---:|---:|---:|
| backend | 1201 | 0 | 17 |
| phase19 | 32 | 0 | 0 |
| postgres | 34 | 0 | 0 |
| backend-contracts | 21 | 0 | 0 |

La suite `backend` est séquentielle, sans xdist, dans l’environnement initial conservé. Elle utilise les versions antérieures des dépendances et les tests de routes antérieurs à leur adaptation ; elle n’est pas une preuve de leur mise à jour. La suite `backend-final` utilise les dépendances corrigées et deux workers pour limiter les ressources. La nouvelle pile complète n’a pas été rejouée séquentiellement : la preuve d’absence de dépendance à l’ordre après mise à jour reste limitée. Les fichiers applicatifs sont comparés par arbres Git ; la différence des dépendances et des tests de routes de la suite initiale est conservée explicitement.
La suite générale utilise SQLite et des simulateurs ; elle ne prouve pas la concurrence PostgreSQL. La sélection `postgres` utilise le moteur réel : callbacks identiques/modifiés concurrents, référence conflictuelle, paiements simultanés, rollback, tenant, charges annulées, course callback/expiration/annulation et cohérence reçu/ledger/statut. La priorité des échéances dispose du test adversarial ajouté lors de la première mission.
Les 17 SKIP de la régression générale concernent les 9 cas de concurrence et 8 cas de contraintes nécessitant la variable PostgreSQL. Leur correspondance individuelle avec la suite réelle est fournie ci-dessous.

- `test_concurrent_identical_callbacks_settle_once` : PostgreSQL séparé **PASS**.
- `test_concurrent_modified_callback_rejected` : PostgreSQL séparé **PASS**.
- `test_concurrent_distinct_payments_do_not_lose_allocation` : PostgreSQL séparé **PASS**.
- `test_concurrent_conflicting_reference_preserves_one_payment` : PostgreSQL séparé **PASS**.
- `test_callback_racing_stale_terminal_save_cannot_erase_settlement[expired]` : PostgreSQL séparé **PASS**.
- `test_callback_racing_stale_terminal_save_cannot_erase_settlement[cancelled]` : PostgreSQL séparé **PASS**.
- `test_terminal_operation_committed_first_blocks_callback[expired]` : PostgreSQL séparé **PASS**.
- `test_terminal_operation_committed_first_blocks_callback[cancelled]` : PostgreSQL séparé **PASS**.
- `test_provider_reference_conflict_rolls_back_second_intent` : PostgreSQL séparé **PASS**.
- `test_migrated_finance_rejects_nonpositive_receipt` : PostgreSQL séparé **PASS**.
- `test_migrated_charge_rejects_overallocation` : PostgreSQL séparé **PASS**.
- `test_migrated_unique_constraints_exist[uq_gateway_idempotency]` : PostgreSQL séparé **PASS**.
- `test_migrated_unique_constraints_exist[uq_gateway_merchant_ref]` : PostgreSQL séparé **PASS**.
- `test_migrated_unique_constraints_exist[uq_gateway_provider_ref]` : PostgreSQL séparé **PASS**.
- `test_migrated_unique_constraints_exist[uq_gateway_provider_event]` : PostgreSQL séparé **PASS**.
- `test_migrated_unique_constraints_exist[uq_finance_external_ref]` : PostgreSQL séparé **PASS**.
- `test_migrated_unique_constraints_exist[uq_finance_reference]` : PostgreSQL séparé **PASS**.

Authentification/restauration de session, permissions, isolation tenant, validation des entrées, journalisation sensible et paiements sont couverts par les tests de la suite complète. Une sélection individuelle des cas exécutés figure dans [SECURITY_COVERAGE.json](evidence/phase19-final/SECURITY_COVERAGE.json), avec les SKIP distincts. Cela reste une validation des scénarios testés, sans pentest externe ni preuve exhaustive de toutes les configurations de déploiement.

## Les 55 audits structurels

Les 17 échecs initiaux ont été reproduits individuellement : [baseline](evidence/phase19-final/baseline/results.json). Décision motivée et cause par audit : [contrats historiques](docs/PHASE19_AUDIT_CONTRACT_DECISION.md). Les anciens journaux restent inchangés. Les minima numériques remplacent uniquement les versions historiques incompatibles ; les contrôles métier restent obligatoires. Les cinq vérifications lexicales ont été remplacées par des vérifications structurelles plus précises. Deux tests négatifs vérifient versions insuffisantes, invalides et métadonnées API débranchées.
Résultat : 55/55 scripts réussis. Les audits structurels ne sont pas des tests fonctionnels.

| Audit | Code | Résultat |
|---|---:|---|
| [audit_campus_intelligence_flutter](evidence/phase19-final/audits/audit_campus_intelligence_flutter.log) | 0 | PASS |
| [audit_lot10_analytics](evidence/phase19-final/audits/audit_lot10_analytics.log) | 0 | PASS |
| [audit_lot10_uiux_maximal](evidence/phase19-final/audits/audit_lot10_uiux_maximal.log) | 0 | PASS |
| [audit_lot11_editorial](evidence/phase19-final/audits/audit_lot11_editorial.log) | 0 | PASS |
| [audit_lot11_maximal](evidence/phase19-final/audits/audit_lot11_maximal.log) | 0 | PASS |
| [audit_lot12_ingestion](evidence/phase19-final/audits/audit_lot12_ingestion.log) | 0 | PASS |
| [audit_lot13_content_factory](evidence/phase19-final/audits/audit_lot13_content_factory.log) | 0 | PASS |
| [audit_lot13_final](evidence/phase19-final/audits/audit_lot13_final.log) | 0 | PASS |
| [audit_lot13_uiux_premium](evidence/phase19-final/audits/audit_lot13_uiux_premium.log) | 0 | PASS |
| [audit_lot14_final](evidence/phase19-final/audits/audit_lot14_final.log) | 0 | PASS |
| [audit_lot14_publication](evidence/phase19-final/audits/audit_lot14_publication.log) | 0 | PASS |
| [audit_lot15_final](evidence/phase19-final/audits/audit_lot15_final.log) | 0 | PASS |
| [audit_lot15_learning_experience](evidence/phase19-final/audits/audit_lot15_learning_experience.log) | 0 | PASS |
| [audit_lot15_student_delight](evidence/phase19-final/audits/audit_lot15_student_delight.log) | 0 | PASS |
| [audit_lot16_adaptive](evidence/phase19-final/audits/audit_lot16_adaptive.log) | 0 | PASS |
| [audit_lot16_final](evidence/phase19-final/audits/audit_lot16_final.log) | 0 | PASS |
| [audit_lot17_planner](evidence/phase19-final/audits/audit_lot17_planner.log) | 0 | PASS |
| [audit_lot18_assessment](evidence/phase19-final/audits/audit_lot18_assessment.log) | 0 | PASS |
| [audit_lot18_cognitive_intelligence](evidence/phase19-final/audits/audit_lot18_cognitive_intelligence.log) | 0 | PASS |
| [audit_lot18_question_factory](evidence/phase19-final/audits/audit_lot18_question_factory.log) | 0 | PASS |
| [audit_lot19_remediation](evidence/phase19-final/audits/audit_lot19_remediation.log) | 0 | PASS |
| [audit_lot19_tutor](evidence/phase19-final/audits/audit_lot19_tutor.log) | 0 | PASS |
| [audit_lot19_v0202](evidence/phase19-final/audits/audit_lot19_v0202.log) | 0 | PASS |
| [audit_lot20_knowledge_graph](evidence/phase19-final/audits/audit_lot20_knowledge_graph.log) | 0 | PASS |
| [audit_lot20_knowledge_graph_v0211](evidence/phase19-final/audits/audit_lot20_knowledge_graph_v0211.log) | 0 | PASS |
| [audit_lot20_knowledge_graph_v0212](evidence/phase19-final/audits/audit_lot20_knowledge_graph_v0212.log) | 0 | PASS |
| [audit_lot21_tutor](evidence/phase19-final/audits/audit_lot21_tutor.log) | 0 | PASS |
| [audit_lot22](evidence/phase19-final/audits/audit_lot22.log) | 0 | PASS |
| [audit_lot22_deep](evidence/phase19-final/audits/audit_lot22_deep.log) | 0 | PASS |
| [audit_lot23](evidence/phase19-final/audits/audit_lot23.log) | 0 | PASS |
| [audit_lot23_maximal](evidence/phase19-final/audits/audit_lot23_maximal.log) | 0 | PASS |
| [audit_lot24](evidence/phase19-final/audits/audit_lot24.log) | 0 | PASS |
| [audit_lot24_closure](evidence/phase19-final/audits/audit_lot24_closure.log) | 0 | PASS |
| [audit_lot25](evidence/phase19-final/audits/audit_lot25.log) | 0 | PASS |
| [audit_lot25_closure](evidence/phase19-final/audits/audit_lot25_closure.log) | 0 | PASS |
| [audit_lot25_maximal](evidence/phase19-final/audits/audit_lot25_maximal.log) | 0 | PASS |
| [audit_lot26](evidence/phase19-final/audits/audit_lot26.log) | 0 | PASS |
| [audit_lot26_closure](evidence/phase19-final/audits/audit_lot26_closure.log) | 0 | PASS |
| [audit_lot26_v0271](evidence/phase19-final/audits/audit_lot26_v0271.log) | 0 | PASS |
| [audit_lot26_v0273](evidence/phase19-final/audits/audit_lot26_v0273.log) | 0 | PASS |
| [audit_lot27](evidence/phase19-final/audits/audit_lot27.log) | 0 | PASS |
| [audit_lot27_final](evidence/phase19-final/audits/audit_lot27_final.log) | 0 | PASS |
| [audit_lot27_v0281](evidence/phase19-final/audits/audit_lot27_v0281.log) | 0 | PASS |
| [audit_lot28](evidence/phase19-final/audits/audit_lot28.log) | 0 | PASS |
| [audit_lot29](evidence/phase19-final/audits/audit_lot29.log) | 0 | PASS |
| [audit_lot29_final](evidence/phase19-final/audits/audit_lot29_final.log) | 0 | PASS |
| [audit_lot30](evidence/phase19-final/audits/audit_lot30.log) | 0 | PASS |
| [audit_lot31](evidence/phase19-final/audits/audit_lot31.log) | 0 | PASS |
| [audit_lot32_global](evidence/phase19-final/audits/audit_lot32_global.log) | 0 | PASS |
| [audit_lot9_ux](evidence/phase19-final/audits/audit_lot9_ux.log) | 0 | PASS |
| [audit_phase16_closure_v0_51_9](evidence/phase19-final/audits/audit_phase16_closure_v0_51_9.log) | 0 | PASS |
| [audit_phase16_library_governance_v0_51_2](evidence/phase19-final/audits/audit_phase16_library_governance_v0_51_2.log) | 0 | PASS |
| [audit_phase16_physical_library](evidence/phase19-final/audits/audit_phase16_physical_library.log) | 0 | PASS |
| [audit_phase16_tenant_policy_v0_51_3](evidence/phase19-final/audits/audit_phase16_tenant_policy_v0_51_3.log) | 0 | PASS |
| [audit_phase16_v0_51_8](evidence/phase19-final/audits/audit_phase16_v0_51_8.log) | 0 | PASS |

## Flutter et builds

Corrections : imports/casts inutiles, blocs de contrôle, champs inutilisés, formulaires `initialValue`, contexte monté après les awaits, prévention de setState après fermeture du détail, migration RadioGroup avec garde de réponse validée. Aucune désactivation globale du linter.
Analyse Admin : voir son code exact dans le tableau. Analyse Mobile : dépréciation de `drift/web.dart` conservée sans suppression ; migrer vers WASM implique assets/worker, compatibilité navigateurs et migration du stockage existant, hors correction mécanique. Cette limite empêche de déclarer `flutter analyze` entièrement réussi.
Les tests Flutter sont exécutés avec un seul worker. Les résumés exacts et erreurs éventuelles figurent dans les journaux mobile-test/admin-test, pas dans un résultat déduit de la compilation.

| Tests Flutter | PASS | FAIL | SKIP |
|---|---:|---:|---:|
| mobile | 96 | 0 | 0 |
| admin | 2 | 0 | 0 |

| Analyse | Erreurs | Avertissements | Informations | Code |
|---|---:|---:|---:|---:|
| mobile | 0 | 0 | 1 | 1 |
| admin | 0 | 0 | 0 | 0 |

| Build | Mode | Code | Artefact | SHA-256 |
|---|---|---:|---|---|
| mobile-web | release | 0 | `apps/mobile/build/web/main.dart.js` (présent : True) | `2128736be2a9efa44ceb97e489acd16714a517049c477c50748ccdbe2d313325` |
| admin-web | release | 0 | `apps/admin/build/web/main.dart.js` (présent : True) | `b4a2ca514e2be2af31b679a34e110b322fd8478d30a350ffeed6d5cc9769b60a` |
| mobile-windows | release | 0 | `apps/mobile/build/windows/x64/runner/Release/edunova.exe` (présent : True) | `c835cb2382a2bf3b18708c87a72d78b6f38fdb42244206705e43f1705d0afa01` |
| admin-windows | release | 0 | `apps/admin/build/windows/x64/runner/Release/edunova_admin.exe` (présent : True) | `6bd81e51799c41c1bc2198187fc852fcae81d29a61d2e5d0dd72e0f719660d76` |
| mobile-android | debug | 0 | `apps/mobile/build/app/outputs/flutter-apk/app-debug.apk` (présent : True) | `e7029554f745f3981dbbb13bcdca682984f35ccd032a6aabb859326b6189a625` |
| admin-android | debug | 0 | `apps/admin/build/app/outputs/flutter-apk/app-debug.apk` (présent : True) | `cdf6309b3248c2bd6e6c4a6ab97af3507e304f9f73149b0eb2dbc8f6af6f176a` |

Les APK sont debug, non signés pour la production. Les exécutables Windows requièrent leur bundle et les builds web leur répertoire complet ; les empreintes ci-dessus identifient les artefacts principaux, pas une signature de déploiement. [BUNDLE_MANIFESTS.json](evidence/phase19-final/BUNDLE_MANIFESTS.json) contient aussi les SHA-256 de tous les fichiers du bundle web et Windows, dont le code AOT. Android : les ABI effectives sont dans [ARTIFACTS.json](evidence/phase19-final/ARTIFACTS.json).

## Dépendances et absence de secrets

Commande : `.venv/Scripts/python.exe -m pip_audit --format=json --output=evidence/phase19-final/dependency-audit.json`. Voir [avis complets](evidence/phase19-final/dependency-audit.json). Les entrées peuvent avoir des doublons ou alias ; elles ne doivent pas être présentées comme autant de vulnérabilités uniques.

| Paquet | Version auditée | Entrées retournées | Identifiants distincts |
|---|---|---:|---:|

Paquets encore signalés par le dernier audit : **0**. Le premier audit signalait 100 entrées (doublons/alias inclus) dans 5 paquets ; les résultats avant correction sont conservés dans [dependency-audit-before-fix.json](evidence/phase19-final/dependency-audit-before-fix.json).
Mises à jour isolées : FastAPI 0.162.0, Starlette 1.10.0, cryptography 50.0.2, Pillow 13.0.0, pytest 9.2.0 ; pip de certification 26.2.2. La simulation de résolution [security-upgrade-resolution.log](evidence/phase19-final/security-upgrade-resolution.log) ne vaut ni installation ni validation ; seuls les résultats des suites corrigées et du nouvel audit font foi. Le scan ne couvre pas automatiquement les dépendances Dart, Android, NuGet ou les bibliothèques natives.
Audit Dart complémentaire via l’[API officielle OSV](https://google.github.io/osv.dev/api/) : 160 couples paquet/version publics ; 0 paquet(s) signalé(s). Réponse incomplète : False. [Résultat exact](evidence/phase19-final/pub-dependency-audit-results.json). Cela ne couvre ni le SDK Flutter ni les binaires natifs transitifs.
Le contrôle [publication-inventory.json](evidence/phase19-final/publication-inventory.json) vérifie les fichiers suivis sans afficher les valeurs détectées. C’est un contrôle heuristique, non une garantie exhaustive. `.env`, cluster PostgreSQL, caches et binaires de build ne sont pas publiés.

## Limites et anomalies restantes

- Paquets Python signalés par le dernier audit : 0. Un résultat vide ne garantit pas l’absence de vulnérabilités inconnues.
- Drift web déprécié ; compilation JavaScript distincte de WASM. Aucun build WASM certifié.
- StudyWorkspacePage et ExamSimulatorPage conservent données illustratives et callbacks vides ; configuration Exam Mode et indication offline ne prouvent pas un parcours métier intégré. Aucun ajout de fonctionnalité pour masquer ce constat.
- iOS/macOS/Linux non exécutés sur Windows. Pas de validation sur appareil physique, de signature release Android, ni de recette visuelle complète des applications natives.
- Providers de paiement, FCM, S3 et Redis de production non testés ; aucun paiement réel, secret de production ou service payant utilisé.
- Pas de pentest ni de charge prolongée ; les invariants financiers sont validés dans les scénarios réels explicitement exécutés.
- Avertissements tiers Python SWIG/PyMuPDF et adaptateur TestClient/httpx déprécié conservés dans les logs ; aucun statut PASS déduit de leur seule absence d’exception.

## Commits de la mission et historiques publiés

La liste ci-dessous couvre les commits locaux depuis l’import de référence ; la visibilité GitHub doit être confirmée après publication. Les messages `[skip ci]` évitent les déclenchements Actions inutiles lors du push.

```text
cfa2ca9ca1dacb9172f49fa85d35cd1c781e2261 cert:local-phase19-harness-and-postgres-regressions
dad0d3160dadeb56522df65c4568dbc628c02a80 fix:lock-terminal-payment-transitions-against-callbacks
9246f18aa93f177a190122a4643fab65b6a778fa cert:preserve-local-attempts-and-record-tested-commit
5e1ee51da3cc58cbe5880a83342184e3e7f7ad7b build:prepare-local-windows-web-and-ocr-certification
eaed691f9660b2a9d0557dd24e50c060d70fbfbc fix:resolve-flutter-syntax-imports-and-notification-api
dd17f3d5a4096fbcedbf755c3896096556aeac12 fix:windows-ingestion-files-and-finance-due-date-allocation
4b2b67fe02449b3cb9d44c38441b3b437e8620f6 fix:preserve-dio-query-parameters-and-sync-error-test-double
05fdeac0e03c3a5a7190470fa18874bd57942269 fix:finish-editorial-api-syntax-and-isolate-flutter-widget-tests
d4169e8b131d313de87b02d2713f5008f879fee3 cert:cover-android-hosts-and-historical-structural-audits
2501a2f200735af9159bb32e4ec037a5ce85b773 cert:finish-login-and-privacy-fixtures-and-native-plugin-registration
a8d1ce603bb9c89ce5a34b4983ac9d0f8155024e test:target-the-institutional-scrollable-in-privacy-check
6d9f4e04e88325aa228334bca30641127be758fd cert:generate-reproducible-local-report-and-failure-appendix
d5375a28c0c8ce706e102ccb64e128460bb36595 fix:recover-windows-bundle-prefix-and-bound-local-build-memory
bee07026f77c0d9ac3a11efa280739db8b005a4d cert:retain-all-failure-attempts-and-verify-build-artifacts
6f85e8cd07b2143d3b8d6419158717651530cf06 fix:enable-android-notification-desugaring-with-java17
79ffe15a4eef6165f8395c0921abc498552c35ee cert:propagate-failed-checks-and-record-delivery-provenance
266b23fa0d63aa97fb3b11b9fd853c2ae3c76755 cert: add local Phase19 certification report and evidence [skip ci]
844749adceb01efb3ab54eef460b4c6533baa688 cert: evolve cumulative audit contracts with negative controls [skip ci]
716a11fcb8c98073e218290bdc020ed98ade5886 fix: remove Flutter warnings and guard async UI lifetimes [skip ci]
793627f1bed4e9b135667c57875ade1df79d575e fix: migrate quiz controls to accessible RadioGroup API [skip ci]
b4a8eabafa7d6a1f50f4cc4cc43fc610a1040fbb cert: isolate fresh migration replay and inspect publication risks [skip ci]
28ef7b33689316c2edb8d8fe692f09695a860e5f fix: update vulnerable Python dependencies for isolated regression [skip ci]
54555d907839a7d51f72393e193c76b6ae97bef5 cert: record final evidence and secure GitHub delivery provenance [skip ci]
edb7876cb26c131ec13c15e33f40b98022801e33 cert: bound updated dependency regression to two workers [skip ci]
9dcb12fa7cb4b16a8b3d6ae13b534a20fd35ae44 test: verify evolved audit contracts through Flutter interactions [skip ci]
50622ede01b1cff0ad993e532859972288b9ddfd test: intercept editorial extension API at HTTP boundary [skip ci]
f92878e7196711cbdbb30eb004f6252a3541eb44 fix: constrain study workspace headings to available width [skip ci]
9424aa1ce5e928aa0e3c5f30daba6ec773c1a509 test: inspect effective FastAPI routes and exercise unauthenticated access [skip ci]
339100bad268775b8e055f8f311535539d3b52bf cert: audit public Dart packages and preserve diagnostic provenance [skip ci]
08d1143736ba014e0822454675d6b9ea3a5d2bd4 docs: distinguish Python and Dart vulnerability audit scopes [skip ci]
```

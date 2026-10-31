# EduNova — certification locale jusqu’à la Phase 19

Rapport généré le 2026-10-31T21:52:54+02:00.

## Verdict : PARTIELLEMENT CERTIFIÉ

Les réussites ci-dessous sont limitées aux contrôles effectivement exécutés. Elles ne clôturent pas automatiquement les Phases 1–19. Les avertissements d’analyse, audits structurels en échec et éventuels builds bloqués restent des réserves.

Bilan terminé pour les commandes listées ; les échecs et limites ci-dessous restent explicites.

## Dépôt et commits

- Dépôt : DANIELKIKUNDA/edunova ; branche import/edunova-v0.57.12.
- Import initial propre : `6607b18da64eb44c2de017192ccefded21659a35`.
- HEAD source lors de la génération : `79ffe15a4eef6165f8395c0921abc498552c35ee`. Les commits exacts de chaque suite sont inscrits dans le tableau et les JSON. Les contrôles couvrent plusieurs commits successifs ; ne pas attribuer tous les anciens résultats à HEAD.
- Dernier commit modifiant les applications ou le backend : `6f85e8cd07b2143d3b8d6419158717651530cf06`. Les commits documentaires ultérieurs ne remplacent pas les références des exécutions.
- PR #1 vérifiée ouverte, non fusionnée et en brouillon. Aucun changement demandé à main.
- Les corrections sont des commits locaux non poussés ; la PR distante est restée sur le commit d’import au dernier contrôle. Ne pas chercher les nouveaux commits sur GitHub avant leur publication explicite.
- Dossier local : `C:/Users/cs-ap/dev/edusync-web/edunova`. Le dépôt parent edusync-web et ses modifications locales sont conservés.

Correspondance des sources exécutées avec la livraison, vérifiée par les identifiants d’arbres Git dans [TREE_IDENTITY.json](evidence/local-phase19/TREE_IDENTITY.json) :

- `services/api/app` : arbre Git identique au commit exécuté `dd17f3d5a4096fbcedbf755c3896096556aeac12` : **True**.
- `services/api/tests` : arbre Git identique au commit exécuté `dd17f3d5a4096fbcedbf755c3896096556aeac12` : **True**.
- `apps/mobile/lib` : arbre Git identique au commit exécuté `d5375a28c0c8ce706e102ccb64e128460bb36595` : **True**.
- `apps/mobile/test` : arbre Git identique au commit exécuté `d5375a28c0c8ce706e102ccb64e128460bb36595` : **True**.
- `apps/admin/lib` : arbre Git identique au commit exécuté `d5375a28c0c8ce706e102ccb64e128460bb36595` : **True**.
- `apps/admin/test` : arbre Git identique au commit exécuté `d5375a28c0c8ce706e102ccb64e128460bb36595` : **True**.
- `apps/mobile/lib` : arbre Git identique au commit exécuté `05fdeac0e03c3a5a7190470fa18874bd57942269` : **True**.
- `apps/mobile/web` : arbre Git identique au commit exécuté `05fdeac0e03c3a5a7190470fa18874bd57942269` : **True**.
- `apps/admin/lib` : arbre Git identique au commit exécuté `05fdeac0e03c3a5a7190470fa18874bd57942269` : **True**.
- `apps/admin/web` : arbre Git identique au commit exécuté `05fdeac0e03c3a5a7190470fa18874bd57942269` : **True**.
- `apps/mobile/lib` : arbre Git identique au commit exécuté `d5375a28c0c8ce706e102ccb64e128460bb36595` : **True**.
- `apps/mobile/windows` : arbre Git identique au commit exécuté `d5375a28c0c8ce706e102ccb64e128460bb36595` : **True**.
- `apps/admin/lib` : arbre Git identique au commit exécuté `6f85e8cd07b2143d3b8d6419158717651530cf06` : **True**.
- `apps/admin/windows` : arbre Git identique au commit exécuté `6f85e8cd07b2143d3b8d6419158717651530cf06` : **True**.
- `apps/mobile/lib` : arbre Git identique au commit exécuté `6f85e8cd07b2143d3b8d6419158717651530cf06` : **True**.
- `apps/mobile/android` : arbre Git identique au commit exécuté `6f85e8cd07b2143d3b8d6419158717651530cf06` : **True**.
- `apps/admin/lib` : arbre Git identique au commit exécuté `bee07026f77c0d9ac3a11efa280739db8b005a4d` : **True**.
- `apps/admin/android` : arbre Git identique au commit exécuté `bee07026f77c0d9ac3a11efa280739db8b005a4d` : **True**.

## Environnement

Windows 11 x64 ; Git 2.51.0.windows.1 ; Python 3.13.14 dans `.venv` ; pytest 9.0.2 ; pytest-xdist 3.8.0 ; PostgreSQL 16.11 ; Flutter 3.35.4 ; Dart 3.9.2 ; Android SDK 36 / Java 21 ; Visual Studio Community 2022 17.14.41. Voir `flutter-doctor.log` pour les détails.

Tesseract 5.5.3.20260724 installé dans `.local-certification/tesseract`, avec eng/fra. Source Windows vérifiée : [documentation UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). NuGet 6.14.0 est téléchargé localement pour flutter_tts. Le composant C++ ATL a été installé et les en-têtes `atlstr.h` vérifiés sur disque ; `atl-install-exit.txt` et `atl-install-verification.txt` conservent la sortie de l’installeur et la confirmation.

Les SDK étaient absents du PATH initial mais présents sur disque. Docker client est installé ; le moteur Docker n’était pas disponible, il n’a pas servi de preuve. Le mode Développeur Windows a ensuite été activé par l’utilisateur.

## Configuration et dépendances

Le clone ne contenait pas de `.env`. Les noms des variables du modèle ont été vérifiés sans afficher de secrets. Le runner retire les variables sensibles héritées, impose le mode test et n’utilise pas de prestataire de paiement réel. Les dépendances Python déclarées ont été installées ; `freeze.log` conserve les versions résolues et `pip-check.log` leur cohérence. Les résolutions Flutter sont conservées dans les fichiers `*-dependencies.lock`. Aucune opération financière réelle ni aucun service payant n’a été utilisé.

Les seules présences de variables, sans valeurs, sont conservées dans [ENVIRONMENT.json](evidence/local-phase19/ENVIRONMENT.json).

## Résultats et commandes

Les nombres des suites se recouvrent : ne pas les additionner comme des tests uniques. La collecte seule et les audits structurels ne sont pas des suites fonctionnelles.

La régression complète finale utilise quatre processus pytest avec répartition par fichier (`--dist loadfile`) et bases séparées. L’ancienne tentative séquentielle est conservée avec ses échecs ; elle n’a pas été intégralement répétée après toutes les corrections. La réussite parallèle ne prouve donc pas à elle seule l’absence de dépendance à l’ordre global des anciens tests.

Audits structurels exécutés : 38 scripts réussis et 17 en échec sur 55. Il s’agit de codes de sortie de scripts, pas d’un total d’assertions fonctionnelles.

| Contrôle | Résultat mesuré | Code | Commit de la tentative | Preuve |
|---|---|---:|---|---|
| compile | Terminé | 0 | `dd17f3d5a4096fbcedbf755c3896096556aeac12` | [compile.log](evidence/local-phase19/compile.log) |
| pip-check | Terminé | 0 | `79ffe15a4eef6165f8395c0921abc498552c35ee` | [pip-check.log](evidence/local-phase19/pip-check.log) |
| migrations | Terminé | 0 | `non enregistré` | [migrations.log](evidence/local-phase19/migrations.log) |
| backend-final | 1201 réussis, 0 échecs/erreurs, 17 ignorés | 0 | `dd17f3d5a4096fbcedbf755c3896096556aeac12` | [backend-final.log](evidence/local-phase19/backend-final.log) |
| backend-contracts | 21 réussis, 0 échecs/erreurs, 0 ignorés | 0 | `d5375a28c0c8ce706e102ccb64e128460bb36595` | [backend-contracts.log](evidence/local-phase19/backend-contracts.log) |
| phase19 | 32 réussis, 0 échecs/erreurs, 0 ignorés | 0 | `d5375a28c0c8ce706e102ccb64e128460bb36595` | [phase19.log](evidence/local-phase19/phase19.log) |
| postgres | 34 réussis, 0 échecs/erreurs, 0 ignorés | 0 | `d5375a28c0c8ce706e102ccb64e128460bb36595` | [postgres.log](evidence/local-phase19/postgres.log) |
| audits | ÉCHEC | 1 | `d4169e8b131d313de87b02d2713f5008f879fee3` | [audits.log](evidence/local-phase19/audits.log) |
| mobile-pub | Terminé | 0 | `4b2b67fe02449b3cb9d44c38441b3b437e8620f6` | [mobile-pub.log](evidence/local-phase19/mobile-pub.log) |
| mobile-codegen | Terminé | 0 | `9246f18aa93f177a190122a4643fab65b6a778fa` | [mobile-codegen.log](evidence/local-phase19/mobile-codegen.log) |
| mobile-analyze | 0 erreurs, 5 avertissements, 45 informations | 1 | `6f85e8cd07b2143d3b8d6419158717651530cf06` | [mobile-analyze.log](evidence/local-phase19/mobile-analyze.log) |
| mobile-test | 94 réussis, 0 échecs, 0 ignorés | 0 | `d5375a28c0c8ce706e102ccb64e128460bb36595` | [mobile-test.log](evidence/local-phase19/mobile-test.log) |
| mobile-web | Terminé | 0 | `05fdeac0e03c3a5a7190470fa18874bd57942269` | [mobile-web.log](evidence/local-phase19/mobile-web.log) |
| mobile-windows | Terminé | 0 | `d5375a28c0c8ce706e102ccb64e128460bb36595` | [mobile-windows.log](evidence/local-phase19/mobile-windows.log) |
| mobile-android | Terminé | 0 | `6f85e8cd07b2143d3b8d6419158717651530cf06` | [mobile-android.log](evidence/local-phase19/mobile-android.log) |
| admin-pub | Terminé | 0 | `4b2b67fe02449b3cb9d44c38441b3b437e8620f6` | [admin-pub.log](evidence/local-phase19/admin-pub.log) |
| admin-analyze | 0 erreurs, 3 avertissements, 22 informations | 1 | `79ffe15a4eef6165f8395c0921abc498552c35ee` | [admin-analyze.log](evidence/local-phase19/admin-analyze.log) |
| admin-test | 1 réussis, 0 échecs, 0 ignorés | 0 | `d5375a28c0c8ce706e102ccb64e128460bb36595` | [admin-test.log](evidence/local-phase19/admin-test.log) |
| admin-web | Terminé | 0 | `05fdeac0e03c3a5a7190470fa18874bd57942269` | [admin-web.log](evidence/local-phase19/admin-web.log) |
| admin-windows | Terminé | 0 | `6f85e8cd07b2143d3b8d6419158717651530cf06` | [admin-windows.log](evidence/local-phase19/admin-windows.log) |
| admin-android | Terminé | 0 | `bee07026f77c0d9ac3a11efa280739db8b005a4d` | [admin-android.log](evidence/local-phase19/admin-android.log) |

Inventaire exhaustif des tentatives instrumentées : [COMMANDS.md](evidence/local-phase19/COMMANDS.md). Toutes les reprises sont archivées sous `*-previous-*`. Les tentatives initiales de lancement, clonage et installation sont décrites ci-dessous et dans les journaux racine d’evidence.

Préparation, installations et commandes de démarrage : [BOOTSTRAP.md](evidence/local-phase19/BOOTSTRAP.md).

## PostgreSQL et finance

Cluster dédié créé par `initdb -D .local-certification/postgres -U edunova_cert --auth=trust --encoding=UTF8 --locale=C`, limité à `127.0.0.1:55439`. Base : `edunova_phase19_test`. Aucune connexion aux bases existantes ou de production. Les 99 migrations 0001–0099 ont été appliquées via `psql -X -v ON_ERROR_STOP=1` ; preuve `migrations.log`.

Le cluster a été arrêté après les essais : `postgres-stop.log`. Le journal serveur et la configuration dédiée sont conservés dans evidence. Les tests négatifs peuvent produire des ERROR PostgreSQL attendues tout en réussissant leurs assertions ; les conclusions de suite restent celles de JUnit.

La régression générale utilise SQLite isolé par processus. Les suites financières PostgreSQL utilisent une variable distincte, validée contre l’adresse/port/base dédiés et un schéma UUID par test ; leurs tables proviennent de SQLAlchemy. Les huit contrôles de contraintes, séparément, interrogent le schéma public réellement migré et testent les rejets d’écritures invalides. Ce découpage ne constitue pas une validation de tout le backend sur PostgreSQL.

Contrôles financiers exécutés : callback identique simultané à quatre transactions ; payload modifié rejeté ; paiements distincts simultanés sans perte d’allocation ; référence externe conflictuelle ; référence fournisseur conflictuelle avec rollback du second intent ; rollback sur erreur d’insertion de grand livre et de mise à jour des frais ; rejet inter-universités ; frais annulés ; reçu inversé ; expiration/annulation avant callback et état obsolète après callback ; cohérence reçu/grand livre/statut ; allocation suivant les échéances et non l’ordre des UUID. Voir les JUnit et les tests `test_phase19_*`.

Résultats individuels de la commande Phase 19 séparée (mocks/SQLite, complétés par la commande PostgreSQL) :

- `test_phase19_payment_hardening.py` : 15 réussis, 0 échecs, 0 ignorés.
- `test_phase19_atomic_finance.py` : 11 réussis, 0 échecs, 0 ignorés.
- `test_phase19_atomic_callback.py` : 6 réussis, 0 échecs, 0 ignorés.

Deux défauts critiques ont été reproduits avant correction : expiration/annulation obsolète écrasant succeeded après comptabilisation, et allocation des frais selon l’ordre des identifiants. Les traces antérieures sont conservées ; la réussite d’une reprise ne supprime pas cette histoire.

## Corrections réalisées

Isolation du fichier SQLite par processus Windows ; mode PostgreSQL de test explicitement limité à la base dédiée ; verrous de transitions terminales ; ordre d’allocation par échéance ; fermeture des fichiers temporaires avant réouverture OCR ; polices de tests portables ; imports Dart manquants ; erreurs de parenthèses ; API notifications 20 et contrainte de version cohérente ; gestion des paramètres Dio ; icônes disponibles ; génération Drift et hôtes web/Windows/Android. Les importants fichiers générés sont identifiés comme tels, sans refonte du domaine.

Les fixtures Flutter ont été adaptées aux interfaces réelles : portée Riverpod et données locales contrôlées, stockage sécurisé simulé, attente de restauration de session, faux dépôts de synchronisation complets, ciblage de la liste défilante. Les assertions de refus inter-tenant, de non-écriture partielle et de masquage sont conservées. Le test d’intervalle easy attend 33 : 10 × 2,5 × 1,3 = 32,5, arrondi Dart existant ; l’algorithme métier n’a pas été modifié pour ce test.

La machine dispose d’environ 6 Go de RAM. Après une tentative de tests interrompue au chargement, le runner Flutter utilise un seul worker ; Gradle est limité à 2 Go et deux workers. Le préfixe CMake par défaut resté en cache après une configuration interrompue est réparé pour installer le bundle dans le dossier de build, sans écrire dans Program Files. Ces modifications sont des corrections de configuration, pas une suppression de tests.

## Artefacts effectivement vérifiés

- `apps/mobile/build/web/main.dart.js` : SHA-256 `b4b977930d5177edafc0c88bc142bd41c6f1c2f9e6f77413aa7267266792a0d1` ; présence vérifiée : True.
- `apps/admin/build/web/main.dart.js` : SHA-256 `7b64454b494c5372e8bbc7e856ac49a74b94ff984e14511bc55f936df8654f00` ; présence vérifiée : True.
- `apps/mobile/build/windows/x64/runner/Release/edunova.exe` : SHA-256 `c835cb2382a2bf3b18708c87a72d78b6f38fdb42244206705e43f1705d0afa01` ; présence vérifiée : True.
- `apps/admin/build/windows/x64/runner/Release/edunova_admin.exe` : SHA-256 `6bd81e51799c41c1bc2198187fc852fcae81d29a61d2e5d0dd72e0f719660d76` ; présence vérifiée : True.
- `apps/mobile/build/app/outputs/flutter-apk/app-debug.apk` : SHA-256 `672353a821ebbe2d3d3b4fccc685560a97710eaaa8e877b6056a82e0bd12ae3d` ; présence vérifiée : True. ABI constatées dans l’APK : arm64-v8a, armeabi-v7a, x86_64.
- `apps/admin/build/app/outputs/flutter-apk/app-debug.apk` : SHA-256 `2c81263c7d732626cfc5fdce7e2ad9293de2cbc7084e6052198999a9fedd5628` ; présence vérifiée : True. ABI constatées dans l’APK : arm64-v8a, armeabi-v7a, x86_64.

La présence et l’empreinte d’un artefact ne certifient ni son lancement sur appareil ni ses services distants. Les fichiers intermédiaires d’un build échoué sont exclus de cette liste.

## Anomalies, traces et correctifs proposés

[FAILURES.md](evidence/local-phase19/FAILURES.md) fait partie de ce rapport : commande, trace, cause probable et correction appliquée/proposée pour chaque échec pytest, Flutter résiduel et audit historique. Les traces complètes restent dans les XML/logs. Les échecs structurels ne sont ni masqués ni convertis en PASS. Leur actualisation doit être précédée d’une revue du contrat concerné.

Les analyses Flutter standard restent non réussies si leur code de sortie vaut 1, même avec zéro erreur compilateur : les avertissements et informations ne sont pas supprimés. Les builds web JavaScript n’attestent pas de la compatibilité Wasm ; les avertissements de dry-run Wasm restent des réserves.

La comparaison exhaustive des types/contraintes ORM contre toutes les migrations PostgreSQL n’a pas été effectuée. Les remboursements, bourses et tous les points de défaillance hors transaction financière centrale n’ont pas fait l’objet d’une campagne concurrente PostgreSQL exhaustive. L’isolation applicative testée ne constitue pas une preuve de politiques RLS ou de résistance à une forte charge.

## Non exécuté et limites

Pas de build iOS/macOS sur Windows ; pas de build Linux dans cet environnement. Pas de certification sur appareils physiques, notifications FCM réelles, prestataires financiers réels, charge longue durée, réseau distribué, Redis/S3 réels ou PostgreSQL de production. Aucun paiement réel n’a été déclenché. Les APK demandés sont des builds debug locaux, pas des releases signées de production. Les identifiants Android générés com.example doivent être remplacés et validés avant diffusion.

Les tests ignorés dans la suite générale sont explicitement visibles dans JUnit ; les tests PostgreSQL opt-in ont leur exécution dédiée. Les échecs initiaux dus au réseau sandbox ont été repris après autorisation. La tentative complémentaire offline admin initialement refusée n’a pas été exécutée ; une nouvelle résolution online a été autorisée après la demande de poursuite de l’utilisateur.

- `services.api.tests.test_phase19_postgres_concurrency::test_concurrent_identical_callbacks_settle_once` : Requires dedicated real PostgreSQL on localhost:55439.
- `services.api.tests.test_phase19_postgres_concurrency::test_concurrent_modified_callback_rejected` : Requires dedicated real PostgreSQL on localhost:55439.
- `services.api.tests.test_phase19_postgres_concurrency::test_concurrent_distinct_payments_do_not_lose_allocation` : Requires dedicated real PostgreSQL on localhost:55439.
- `services.api.tests.test_phase19_postgres_concurrency::test_concurrent_conflicting_reference_preserves_one_payment` : Requires dedicated real PostgreSQL on localhost:55439.
- `services.api.tests.test_phase19_postgres_concurrency::test_callback_racing_stale_terminal_save_cannot_erase_settlement[expired]` : Requires dedicated real PostgreSQL on localhost:55439.
- `services.api.tests.test_phase19_postgres_concurrency::test_callback_racing_stale_terminal_save_cannot_erase_settlement[cancelled]` : Requires dedicated real PostgreSQL on localhost:55439.
- `services.api.tests.test_phase19_postgres_concurrency::test_terminal_operation_committed_first_blocks_callback[expired]` : Requires dedicated real PostgreSQL on localhost:55439.
- `services.api.tests.test_phase19_postgres_concurrency::test_terminal_operation_committed_first_blocks_callback[cancelled]` : Requires dedicated real PostgreSQL on localhost:55439.
- `services.api.tests.test_phase19_postgres_concurrency::test_provider_reference_conflict_rolls_back_second_intent` : Requires dedicated real PostgreSQL on localhost:55439.
- `services.api.tests.test_phase19_postgres_constraints::test_migrated_finance_rejects_nonpositive_receipt` : Requires the locally migrated certification PostgreSQL database.
- `services.api.tests.test_phase19_postgres_constraints::test_migrated_charge_rejects_overallocation` : Requires the locally migrated certification PostgreSQL database.
- `services.api.tests.test_phase19_postgres_constraints::test_migrated_unique_constraints_exist[uq_gateway_idempotency]` : Requires the locally migrated certification PostgreSQL database.
- `services.api.tests.test_phase19_postgres_constraints::test_migrated_unique_constraints_exist[uq_gateway_merchant_ref]` : Requires the locally migrated certification PostgreSQL database.
- `services.api.tests.test_phase19_postgres_constraints::test_migrated_unique_constraints_exist[uq_gateway_provider_ref]` : Requires the locally migrated certification PostgreSQL database.
- `services.api.tests.test_phase19_postgres_constraints::test_migrated_unique_constraints_exist[uq_gateway_provider_event]` : Requires the locally migrated certification PostgreSQL database.
- `services.api.tests.test_phase19_postgres_constraints::test_migrated_unique_constraints_exist[uq_finance_external_ref]` : Requires the locally migrated certification PostgreSQL database.
- `services.api.tests.test_phase19_postgres_constraints::test_migrated_unique_constraints_exist[uq_finance_reference]` : Requires the locally migrated certification PostgreSQL database.

## Commits de travail

```text
79ffe15a4eef6165f8395c0921abc498552c35ee cert:propagate-failed-checks-and-record-delivery-provenance
6f85e8cd07b2143d3b8d6419158717651530cf06 fix:enable-android-notification-desugaring-with-java17
bee07026f77c0d9ac3a11efa280739db8b005a4d cert:retain-all-failure-attempts-and-verify-build-artifacts
d5375a28c0c8ce706e102ccb64e128460bb36595 fix:recover-windows-bundle-prefix-and-bound-local-build-memory
6d9f4e04e88325aa228334bca30641127be758fd cert:generate-reproducible-local-report-and-failure-appendix
a8d1ce603bb9c89ce5a34b4983ac9d0f8155024e test:target-the-institutional-scrollable-in-privacy-check
2501a2f200735af9159bb32e4ec037a5ce85b773 cert:finish-login-and-privacy-fixtures-and-native-plugin-registration
d4169e8b131d313de87b02d2713f5008f879fee3 cert:cover-android-hosts-and-historical-structural-audits
05fdeac0e03c3a5a7190470fa18874bd57942269 fix:finish-editorial-api-syntax-and-isolate-flutter-widget-tests
4b2b67fe02449b3cb9d44c38441b3b437e8620f6 fix:preserve-dio-query-parameters-and-sync-error-test-double
dd17f3d5a4096fbcedbf755c3896096556aeac12 fix:windows-ingestion-files-and-finance-due-date-allocation
eaed691f9660b2a9d0557dd24e50c060d70fbfbc fix:resolve-flutter-syntax-imports-and-notification-api
5e1ee51da3cc58cbe5880a83342184e3e7f7ad7b build:prepare-local-windows-web-and-ocr-certification
9246f18aa93f177a190122a4643fab65b6a778fa cert:preserve-local-attempts-and-record-tested-commit
dad0d3160dadeb56522df65c4568dbc628c02a80 fix:lock-terminal-payment-transitions-against-callbacks
cfa2ca9ca1dacb9172f49fa85d35cd1c781e2261 cert:local-phase19-harness-and-postgres-regressions
```

Les preuves et ce rapport peuvent être ajoutés dans un commit documentaire ultérieur. Vérifier `git status`, la liste des commits locaux et leur présence distante avant toute reprise. Aucune fusion dans main n’est effectuée.

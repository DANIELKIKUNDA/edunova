# EduNova — Phase 21.A : audit initial des parcours et de la couverture

**Date :** 6 novembre 2026  
**Source :** `a7407415536ead5e16b633ff9adda93f4750ef7b`, branche `import/edunova-v0.57.12`  
**Nature :** audit statique de l'arborescence et de fichiers ciblés via GitHub. **Aucun nouveau test Phase 21 exécuté ici.**  
**Notation :** **EXISTANT** = code/tests identifiés ; **À PROUVER** = scénario intégré manquant ou à confirmer ; **BLOQUANT P0** = preuve requise pour le verdict de Phase 21.

## 1. Inventaire vérifié

| Domaine | Éléments existants observés | Niveau de preuve actuel | Priorité Phase 21 |
| --- | --- | --- | --- |
| Identité / session | `identity/api/router.py` : register, login, refresh, logout, me, sessions, revoke, logout-all, change-password, recovery ; `test_identity_security.py` : 10 tests couvrant rotation, rejeu et révocation | Tests API existants ; **pas de parcours navigateur→API→DB prouvé** | **P0** |
| Premium / commerce | `test_commerce_api_e2e.py` avec paiement sandbox et reçu ; `test_phase18_paid_checkout_flow.py` (fulfillment, refus, idempotence et renouvellement) ; écran `premium_page.dart` | Tests backend et code UI repérés ; **intégration mobile / fournisseur externe non attestée** | **P0** |
| Mobile Money / callbacks | `payment_gateway/api/router.py` avec signature obligatoire, endpoints intents/callbacks/observations/reconciliation ; `test_payment_gateway_phase7.py`, `test_phase19_atomic_callback.py`, `test_phase19_payment_hardening.py` | Nombreux scénarios serveur anti-rejeu, signature, rollback ; **aucune transaction réelle autorisée** | **P0** |
| Synchronisation offline | `sync/api/router.py` avec devices/push/bootstrap/pull/ack ; `test_sync_lot7.py` couvre rejouabilité, conflits, isolation comptes, compaction et appareils ; `cloud_sync_use_case_test.dart`, `sync_push_integrity_test.dart` | Couverture API et client séparée ; **à prouver en scénario réseau coupé → données conservées → reconnexion → DB unique** | **P0** |
| Ingestion PDF / OCR | `ingestion/api/router.py` avec lots, fichiers, traitement/retry; modules `ingestion` et `document_engine` ; tests sous `services/api/tests/ingestion`, `document_engine` et `import_personal_document_test.dart` | Flux éditorial de lots et flux document personnel **à distinguer** ; validation multi-étapes et confidentialité client/serveur à prouver | **P0** |
| Rôles administration / éditorial | Application `apps/admin`, modules `editorial`, `publication`, `platform_governance` ; tests Flutter admin et gouvernance Phase 17 | API / widgets couverts partiellement ; **parcours réels owner/editor/reviewer/publisher à établir** | **P0** |
| Multi-université | Modules campus/identity, tests Phase 16–19, politiques et tests PostgreSQL 16 Phase 20 | Contrôles ciblés présents ; **matrice adversariale API + UI + cache cross-tenant pas encore démontrée de bout en bout** | **P0** |
| Web E2E | `tests/e2e/phase20-web.spec.js` (4 tests sur démarrage, viewport, application active offline et budget de transfert), `playwright.config.js` | **4/4 déjà réussis Phase 20**, mais ce sont des smoke tests ; aucun test fonctionnel métier Web E2E identifié dans ce dossier | **P0** |
| Builds / distribution | Workflow Phase 20 : Android APK, Windows, Linux et iOS simulateur ; artefacts produits | **Compilations réussies**, mais APK signé debug, iOS non signé pour appareil et essais physiques absents | P1 / blocage avant stores |

### Sources directes

- [Routes identité](https://github.com/DANIELKIKUNDA/edunova/blob/import/edunova-v0.57.12/services/api/app/modules/identity/api/router.py) · [Tests identité](https://github.com/DANIELKIKUNDA/edunova/blob/import/edunova-v0.57.12/services/api/tests/test_identity_security.py)
- [Routes paiement](https://github.com/DANIELKIKUNDA/edunova/blob/import/edunova-v0.57.12/services/api/app/modules/payment_gateway/api/router.py) · [Tests callbacks atomiques](https://github.com/DANIELKIKUNDA/edunova/blob/import/edunova-v0.57.12/services/api/tests/test_phase19_atomic_callback.py)
- [Routes synchronisation](https://github.com/DANIELKIKUNDA/edunova/blob/import/edunova-v0.57.12/services/api/app/modules/sync/api/router.py) · [Tests synchronisation](https://github.com/DANIELKIKUNDA/edunova/blob/import/edunova-v0.57.12/services/api/tests/test_sync_lot7.py)
- [Routes ingestion](https://github.com/DANIELKIKUNDA/edunova/blob/import/edunova-v0.57.12/services/api/app/modules/ingestion/api/router.py) · [E2E Phase 20](https://github.com/DANIELKIKUNDA/edunova/blob/import/edunova-v0.57.12/tests/e2e/phase20-web.spec.js)

## 2. Décision technique issue de l'audit

**Ne pas re-développer inutilement les modules déjà présents.** Concentrer les changements sur les interfaces, leur intégration backend/PostgreSQL et la démonstration de parcours réels. Les scénarios API existants doivent servir de filet de non-régression.

**Premier objectif d'implémentation proposé :** harnais de recette P0 pour une session authentifiée sur une base PostgreSQL éphémère, puis scénario utilisateur à assertions réelles couvrant login/session/absence d'accès interdit. Le parcours Mobile Money reste simulé et tout secret de fournisseur absent du dépôt.

**Point de vigilance :** l'ingestion éditoriale des lots PDF n'est pas identique à l'import de cours privés par l'étudiant ; documenter la frontière exacte des deux avant les tests de confidentialité.

## 3. Preuves à construire pour l'acceptation de 21.A

- Documenter la séquence d'actions, les appels API, les tables/états attendus et le résultat observable de chaque scénario P0.
- Pour chaque scénario, identifier son niveau de test existant (unitaire, API, widget, intégration PostgreSQL, navigateur E2E, appareil physique).
- Ajouter des tests au bon niveau; ne pas déclarer « E2E certifié » si l'assertion vérifie seulement un `<body>` visible.
- Enregistrer le commit de code testé, JUnit, captures, journaux expurgés, résultat GO/NO-GO.

**Verdict de cet audit :** cadrage initial effectué. La Phase 21 est **EN COURS** ; aucune recette fonctionnelle complète ne peut encore être déclarée PASS.

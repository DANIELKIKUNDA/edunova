# EduNova_v0.50.0 — Rapport technique / Phase 15 — Foundation

Date de l'itération : 14 octobre 2026.

## Chaîne canonique et périmètre

Source : `EduNova_v0.49.13_RC_PHASE14_BACKEND_CLOSURE.zip` (SHA-256 vérifié : `ab8aed8c45a9a788266ffc23b02a73d4dda6f6cdb3113a605ead40a79cfdbb43`).
Phase 14 backend local conservée ; **Phase 15 commencée mais non close**. Pas de nouvelle roadmap, pas de reconstruction de `institutional_analytics` (module déjà présent, Lot 27, SQL 0045–0047). 

## Code réellement modifié

- `services/api/app/modules/institutional_analytics/api/router.py` : nouvelle route authentifiée `GET /v1/institutional-analytics/institutions/{iid}/intelligence/decision-brief`.
- `services/api/app/modules/institutional_analytics/application/service.py` : RBAC institutionnel pour décision, filtrage rigoureux unité/faculté, cohorte/offre/période, projection explicable, qualité des métriques, suppression petites cellules, absence de décision automatisée, audit de consultation.
- `services/api/app/modules/institutional_analytics/infrastructure/sqlalchemy_repo.py` : comptage des personnes distinctes sur cohortes actives, projection gouvernée alternative au contrat historique Lot 27. Exclusion des présences non validées, données d'un autre tenant, soumissions de non-inscrits, notes non publiées ou non validées ; contrôle de contributeurs distincts pour présences/résultats.
- `services/api/tests/test_phase15_institutional_intelligence.py` : **15 tests nouveaux**, dont erreurs de périmètre, RBAC, étanchéité tenant, fausses affiliations, notes d'une autre université, doublons d'inscription, mono-contributeur de 3 présences ou de 3 examens, gradebook non publié, lecture sans mutation.
- `docs/PHASE15_INSTITUTIONAL_INTELLIGENCE_FOUNDATION_v0.50.0.md` : spécification et limites ; `docs/PHASE15_CHECKPOINT_v0.50.0.md` : point de reprise.

## Résultats exécutés (et limites)

- Pré-développement, source v0.49.13 : **770/770 PASS**, code 0.
- Suite Phase 15 : **15/15 PASS** après correction de deux fixtures de test non conformes aux règles préexistantes (période parent, rôle faculté associé à une unité).
- Régression finale séquentielle et isolée : **785/785 PASS** (160,91 s), code 0.
- Audit structurel historique `scripts/audit_lot32_global.py` : **17/17 PASS**, code 0.
- `python -m compileall -q services/api/app services/api/tests` : PASS, code 0.
- Migrations SQL : aucun ajout ; dernière migration `0084`.

Une première exécution globale post-développement avait produit 70 FAIL / 713 PASS à cause d'une **collision de bases de tests SQLite** : une suite ciblée lancée pendant la régression globale a supprimé le même fichier partagé `.pytest_edunova.db` par son `conftest.py` ; les échecs sont `sqlite3.OperationalError: attempt to write a readonly database`. Le rerun final a été réalisé **sans aucune suite de tests parallèle**, a réussi intégralement (785 PASS), et remplace cet essai non concluant. Aucun échec de ce dernier run n'est caché.

**Non exécuté** : compilation Flutter/Dart, vérification sur appareil physique, migrations sur PostgreSQL réel, Redis réel, stockage objet, fournisseurs, conformité juridique des signatures.

## Mise en garde de confidentialité

Le seuil de trois apprenants distincts et les règles de contributeurs réduisent le risque de divulgation de petites cellules, **sans garantir une anonymisation formelle**. Les requêtes recouvrant différents périmètres permettent éventuellement des soustractions d'agrégats ; aucun mécanisme anti-différenciation multi-requêtes n'est encore certifié. Endpoint réservé aux personnels autorisés. N'interpréter les signaux ni comme des diagnostics d'étudiant ni comme des preuves de causalité. Les résultats académiques et les délibérations restent non modifiés.

## Reprise prévue de Phase 15

Historisation comparable entre périodes, protection anti-différenciation des agrégats recouvrants, provenance et complétude par source, agrégats de gouvernance et interface exécutive. Pas de clôture de Phase 15 à ce stade.

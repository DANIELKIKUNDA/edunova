# EduNova v0.49.12 — Phase 14 : provenance du barème figée à la correction

**Continuation canonique :** `EduNova_v0.49.11_RC_PHASE14_SCORE_RECONCILIATION.zip`, SHA-256 vérifié `ea790751bd6cc798f1486ded5391290e22264fd235149649963df50b0bbd5655`.

**Périmètre :** approfondissement de l'intelligence pédagogique. Phases 0–13 conservées ; aucune ouverture de Phase 15. Aucune reconstruction du gradebook, du jury ni du moteur d'évaluation.

## Défaut identifié sur le code réel

Le contrat `grading_contract_version=1` de v0.49.11 vérifiait la somme totale des questions, mais la lecture historique confrontait à nouveau chaque question à **son barème et à son cours actuels** et utilisait le **seuil actuel du blueprint**. Une modification autorisée d'un barème postérieurement à la correction, un déplacement ou la suppression d'une question pouvait donc invalider les preuves correctes au moment de la notation. Ce mécanisme ne modifiait pas la note, mais privait les enseignants des signaux historiques issus d'une correction vérifiée.

## Modifications réellement implémentées

1. **Contrat de notation v2** : à chaque nouvelle correction automatique cohérente, persistance transactionnelle d'un `grading_snapshot` (identifiant tentative, blueprint, cours, seuil de réussite, ordre/IDs des questions et points canoniques). Empreinte SHA-256 du JSON canonique (`grading_snapshot_sha256`). Schéma explicite, champs typés strictement, aucune prise en charge implicite d'une future méthode de notation non documentée.
2. **Revalidation indépendante du catalogue actuel** : la projection pédagogique v2 recalcule la preuve à partir du snapshot validé, de la tentative notée et des totaux/questions de résultat, plutôt que de l'état courant des questions. Les modifications de points, transferts de cours ou suppressions postérieures n'effacent donc pas automatiquement la preuve de notation initiale.
3. **Historique préservé** : les résultats v0 `legacy_unverified` et v1 `verified_auto_sum` restent dans leur contrat d'origine ; aucun backfill de snapshot historique, aucune réécriture de note officielle. Les résultats v1 continuent d'être comparés au catalogue actuel et peuvent perdre la qualification « vérifiés » après une modification de barème.
4. **Labels pédagogiques** : `verified_snapshot_v2`, `verified_auto_sum`, `mixed_verified_contracts`, `mixed_verified_and_legacy`, `legacy_unverified`, `suppressed` pour les petits effectifs. Les nouvelles preuves sont exploitées dans l'analyse par objectif, la chronologie et les erreurs récurrentes sous les mêmes restrictions de cohorte et d'autorisation.
5. **Validation d'écriture renforcée** : un résultat destiné à une autre tentative et une finalisation revendiquant un autre blueprint sont rejetés avant publication. Relecture des sources officielles et acquisition de verrous de lecture `FOR SHARE` sur barèmes et blueprint dans la transaction (en PostgreSQL ; non certifié sur PostgreSQL réel).
6. **Migration SQL `0084_assessment_grading_snapshot_v0_49_12.sql`** : colonnes JSONB et SHA-256 facultatives pour anciens contrats, obligatoires pour le nouveau, extension du contrôle `grading_contract_version IN (0,1,2)`. Vérification contractuelle statique seulement dans l'environnement présent.

## Couverture des tests

Les tests ajoutés portent sur : génération en écriture réelle SQLite, égalité du snapshot et du barème d'origine, modification/suppression/transfert des questions après correction, seuil de réussite modifié, conservation v1 et legacy sans promotion, SHA incohérent, JSON altéré, barème falsifié même avec SHA recalculé, doublon, tentative/blueprint/cours contradictoires, résultats détaillés invalides, permissions enseignants, séparation des universités, masquage des effectifs inférieurs à trois et atomicité en cas de falsification.

Voir `docs/certification/PHASE14_GRADING_SNAPSHOT_v0.49.12_TEST_EVIDENCE.txt` pour les commandes et résultats obtenus, sans extrapolation aux composants non exécutés.

## Limites et garde-fous explicites

- Le SHA-256 **n'est pas une signature** : un administrateur ayant un accès direct en écriture à la base pourrait modifier simultanément la preuve et son empreinte. La journalisation immuable externe et la sécurité DBA relèvent de l'industrialisation/certification.
- Le snapshot v2 capture le **barème utilisé pour corriger**, pas nécessairement le contenu et la clé de réponse affichés au début de la tentative. Leur archivage de bout en bout et les corrections manuelles, bonus ou modérations requièrent des contrats supplémentaires.
- Les liens question→objectif pédagogique restent gérés par une cartographie institutionnelle distincte. Le snapshot des points ne prouve pas à lui seul l'historique de cette cartographie. Un blueprint déplacé hors de son cours actuel est volontairement exclu du périmètre d'analyses.
- La correspondance automatique entre `assessment_results` et les notes **publiées séparément dans gradebook/jury** n'est **pas** établie par ce chantier. Aucun résultat officiel n'est recalculé ni publié.
- Les validations Flutter, appareil, PostgreSQL réel (migrations et verrous), Redis, stockage objet et fournisseurs externes ne sont pas revendiquées. Phase 14 reste ouverte.

## Résultats réellement exécutés dans l’environnement ChatGPT

| Vérification | Résultat |
|---|---|
| Source v0.49.11 extraite, régression avant changement | 727/727 PASS, code 0, 44,61 s |
| Code v0.49.12, régression complète finale | **752/752 PASS**, code 0, 50,80 s |
| Phase 14 + migration, tests ciblés | **132/132 PASS**, code 0, 18,69 s |
| Contrat de migrations | 1/1 PASS, code 0, 0,70 s |
| Audit structurel existant `scripts/audit_lot32_global.py` | **17/17 PASS**, code 0 |
| Compilation bytecode Python `compileall` | code 0 |
| Ajout de tests backend | **25 cas** supplémentaires par rapport à v0.49.11 |

**Commandes principales :** `PYTHONPATH=services/api python -m pytest -q services/api/tests` ; `python -m compileall -q services/api/app services/api/tests` ; `python scripts/audit_lot32_global.py`. La certification de la migration sur PostgreSQL réel n'a pas été exécutée.

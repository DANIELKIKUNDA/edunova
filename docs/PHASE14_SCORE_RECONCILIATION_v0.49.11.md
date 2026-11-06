# EduNova v0.49.11 — Phase 14 : réconciliation vérifiable des notes et questions

**Source canonique :** `EduNova_v0.49.10_RC_PHASE14_ATTEMPT_RESULT_INTEGRITY.zip` — SHA-256 vérifié `e36fc837abc9745731f90f8df9c390542939c5d06bde3e88a7f52d3a6ed3c1ec`.

**Périmètre :** continuation de la Phase 14, sans reconstruire les phases 0–13 et sans engager la Phase 15. Les systèmes de notes officielles, gradebook et jury ne sont pas recalculés ou modifiés par la projection d'intelligence pédagogique.

## Problème concret reproduit

Le modèle historique `assessment_results` conserve un total (`earned`, `possible`, `percent`, `passed`) et une liste JSON `questions`, mais **n'indique pas si celle-ci est exhaustive**. Les anciennes données peuvent stocker une note globale 50/100 et un seul détail de question noté 20/20, sans preuve concernant les autres questions. L'ancienne projection utilisait les détails valides pour des analyses par objectif, ce qui ne constitue pas une preuve de réconciliation exhaustive. Une simple égalité des sommes n'aurait pas suffi à établir l'exhaustivité.

## Modifications implémentées

1. Nouveau contrat **`grading_contract_version`** : `0 = legacy_unverified` (toutes les données historiques, migration non destructive), `1 = verified_auto_sum` réservé aux corrections automatiques additives complètes. Migration SQL versionnée `0083_assessment_auto_sum_evidence_contract_v0_49_11.sql`; nouvelles notes écrites en `1` seulement après contrôle. Les anciennes notes ne sont **pas** requalifiées automatiquement.
2. Vérificateur partagé `assessment/domain/score_integrity.py` : vérification de la présence unique de chaque question de la tentative (y compris celles non cartographiées sur un objectif), de son rattachement au cours, des points autorisés, des champs numériques, du verdict binaire, des sommes exactes, du pourcentage arrondi conformément au correcteur et du seuil d'admission du blueprint. Aucun bonus, note manuelle ou autre transformation n'est prétendu couvert par v1 : ils nécessiteront une version contractuelle explicite.
3. **Écriture atomique** dans le dépôt SQL des évaluations : validation du contrat, contrôle de la version optimiste et de l'état actif, passage à l'état noté et insertion du résultat dans **la même transaction**. Un échec (incohérence, écriture concurrente ou doublon) ne laisse pas une tentative « notée » sans résultat. La voie historique `save_result` est conservée sous validation stricte et interdit la réécriture d'une note déjà existante.
4. Projections `objective_signals` et `objective_trends` : le contrôle **complet** s'applique aux résultats v1 avant leur agrégation. Un v1 incomplet, altéré, de cours différent ou de version inconnue est exclu sans revenir vers une ancienne reprise. Les détails v0 restent éventuellement exploitables comme **signaux historiques non exhaustivement vérifiés**, mais reçoivent la qualification `legacy_unverified` (ou `mixed_verified_and_legacy`).
5. API enseignants : `evidence_integrity` est visible sur les analyses par objectif, tendances et erreurs récurrentes, et est **masqué** pour les cellules de moins de trois étudiants. Les alertes fondées en tout ou partie sur des preuves historiques voient leur confiance rétrogradée à `low` avec avertissement explicite. Aucun identifiant personnel nouveau n'est exposé.
6. Gardes de correction en amont : question supprimée, points invalides, doublon dans la tentative ou question réaffectée à un autre cours provoquent un échec contrôlé avant finalisation.

## Tests et confidentialité

- Régression backend de référence extraite du ZIP v0.49.10 : **698/698 PASS**.
- Régression backend après changements : **727/727 PASS**.
- Tests spécifiques Phase 14, ancienne + nouvelle suite : **106/106 PASS** (77 historiques + 29 nouveaux).
- Contrat de migrations : **1/1 PASS**.
- Compilation `compileall` Python : **PASS**.
- Tests adversariaux : détails manquants, dupliqués, étrangers, incohérence `earned/possible/percent/passed`, valeurs `NaN`, changement de barème ou de cours, contrat futur inconnu, tentative impossible, course/tenant distinct, petits groupes et absence de publication partielle après rejet.
- Isolation multi-universités et rôle enseignant : validés par tests SQL SQLite locaux et contrôles applicatifs (dont refus des membres non autorisés).

Voir `docs/certification/PHASE14_SCORE_RECONCILIATION_v0.49.11_TEST_EVIDENCE.txt`.

## Limites déclarées

- **Historique :** l'absence de détail exhaustif ne peut pas être réparée par calcul : v0 conserve son statut non certifié ; aucune migration des notes existantes n'est effectuée.
- **Auto-sum seulement :** le contrat v1 ne constitue pas un moteur de modération, d'arrondi spécial, de bonus ni de correction humaine. Ne pas l'employer pour de tels barèmes sans version supplémentaire.
- **Évolutions du catalogue :** la revalidation en lecture utilise les points/affectations actuellement canoniques ; après modification de catalogue, une évaluation v1 historique peut être exclue des analyses tant qu'une politique d'archivage du barème original n'est pas implémentée. Cela ne modifie pas la note officielle.
- **Certification :** tests SQLite et Python réalisés ici ; aucune preuve de compilation Flutter, de vérification sur appareil, de migration sur PostgreSQL réel, de Redis, stockage objet, fournisseurs externes ou signature légale qualifiée. Pas de gel v1.0 ni de clôture de Phase 14.

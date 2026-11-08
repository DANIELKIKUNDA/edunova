# EduNova v0.49.13 — Phase 14 : clôture fonctionnelle backend / certification statique locale

Date : 2026-10-13. Source canonique : `EduNova_v0.49.12_RC_PHASE14_GRADING_SNAPSHOT.zip` ; SHA-256 vérifié : `651dd03633b61bfe5718c8ad0a7bba6d1aa4109a4e434605384ef0f0e97e8b19`.

## Décision de périmètre

La **Phase 14 — Intelligence pédagogique** est close *au niveau de l'implémentation backend et des vérifications statiques/locales disponibles* : règles déterministes explicables, analyse du cours et des objectifs, tendances, erreurs récurrentes, dashboard enseignant, contrôles de provenance, horodatage de la cartographie, agrégation protégée, comparaison informative avec des références candidates de notes de gradebook. **Cette clôture n'est PAS une certification de déploiement sur PostgreSQL/Redis réel, appareils Flutter, ni une authentification légale des résultats académiques.** Ce constat ne clôt ni la Phase 22, ni 23, ni les autres phases prévues.

La plateforme conserve des modules indépendants préexistants (adaptive learning, tutor, planning, knowledge graph, évaluations, gradebook, jury) ; aucune reconstruction, aucun recalcul de note ou écriture de résultat officiel.

## Évolutions apportées après v0.49.12

### 1. Historique de la relation question → objectif

La carte d'objectifs dispose déjà d'une association insérée de manière immuable par l'API et d'un horodatage `created_at`. Les projections SQL vérifient maintenant, pour chaque preuve exploitée, si l'association existait **avant le début de la tentative**, **durant la tentative mais avant sa soumission**, **après soumission** ou avec une datation **inconnue**. Ce critère est ajouté aux agrégats et tendances via `mapping_provenance`, distinct de `evidence_integrity` (validité du résultat de notation).

Une cartographie rétrospective n'est **pas** présentée comme une preuve des objectifs attribués lors du passage de l'épreuve : les avertissements enseignant abaissent explicitement la confiance, y compris lorsqu'une note porte un snapshot de barème v2 vérifié. Les cellules de moins de trois apprenants masquent également le nouvel indicateur.

Limite voulue : l'horodatage et l'association ne forment pas une archive signée de la *présentation* du questionnaire à l'étudiant. Le contrat v2 gèle les points utilisés à la correction ; l'interface ne prétend pas à davantage. Les administrateurs de base de données conservent des capacités externes au contrat applicatif.

### 2. Réconciliation **informative et non autoritative** avec le gradebook publié

Nouvelle route staff seulement : `GET /pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/gradebook-reconciliation` (préfixe de montage à confirmer par l'application). L'implémentation se trouve dans `SqlObjectiveEvidenceRepository.gradebook_assessment_reconciliation` ; elle n'écrit **aucune** note.

Elle inspecte seulement les notes validées issues de composants `exam`/`test` d'un gradebook **publié**, et uniquement les références candidates rédigées exactement sous la forme `assessment:<attempt_id>`. Vérifications : établissement + offre + cohorte active, blueprint lié à la même offre, cours, auteur de la tentative, statut soumis/noté, contrat auto-sum v2, empreinte du barème et cohérence du score ramené sur le barème du composant (tolérance documentée de 0,51 point de pourcentage pour les arrondis). Une référence répétée, un compte ou un cours étranger, un score impossible ou un résultat historique non certifié conduisent au statut `manual_review_required`. Aucune identité, note individuelle ni référence d'évaluation n'est retournée. Groupe <3 : valeurs sensibles masquées.

**Important :** `source_ref` du gradebook est saisi par un membre du personnel et ne constitue pas une liaison officiellement authentifiée. Même `candidate_scores_consistent` signifie uniquement « cohérence numérique des références candidates examinées ». Le résultat expose systématiquement `authoritative_source_link=false`, `official_grade_modified=false` et ses limites. Cette route **ne prouve pas** la correspondance de tous les composants du gradebook, ni la publication officielle finale et ne déclenche aucune décision du jury.

### 3. Contrôles inchangés et acquis v0.49.0–v0.49.12

Isolation multi-institutions, périmètre offert / cohorte active, rôles enseignant et administration, suppression des effectifs inférieurs à trois, absence de diagnostic individuel, interprétation prudente des résultats historiques incomplets, sélection d'une seule reprise d'évaluation par compte et blueprint, exclusion des données malformées, provenance de la notation automatique, snapshot immuable du barème à la correction, atomicité de cette correction.

### 4. Sécurité et tests adversariaux ajoutés

Scénarios à base SQL SQLite, avec compte d'une autre université, modification du score, résultat sans contrat fiable, empreinte frauduleuse, duplications de référence, changement d'offre/blueprint, score non fini, données de petit groupe, examen non publié, absence de rôle staff et mapping rétrospectif. Les tests couvrent également le maintien des notes officielles sans réécriture.

## Limites explicitement exclues de la certification locale

- Les tests d'intégration SQL sont principalement SQLite ; ne prouvent ni migrations PostgreSQL en production, ni efficacité des verrous PostgreSQL, ni Redis, ni stockage objet.
- SDK Flutter/Dart et outils PostgreSQL/Redis absents de cet environnement de travail ; aucune compilation ou certification sur appareil n'est revendiquée.
- Les signatures électroniques qualifiées, archivage externe immuable, délégations officielles du jury et fournisseurs tiers ne sont pas certifiés.
- Correction manuelle, bonus, modérations et vieilles évaluations incomplètes ne sont pas déclarés automatiquement compatibles avec le contrat auto-sum v2 ; leurs données restent protégées et identifiées, sans reconstruction fictive.
- La correspondance **authentifiée** entre notes du gradebook, résultats de l'évaluation et décision officielle du jury n'est pas inventée à partir d'un `source_ref` libre. Une future intégration autoritative doit définir un acte de publication transactionnel, traçable et soumis aux permissions académiques ; ce travail n'est pas couvert par la route de lecture informative.
- Aucune prétention de conformité Caliper ou autre standard d'interopérabilité ; la séparation preuves d'évaluation / notation correspond seulement au principe de traçabilité.

## Certification et passage vers Phase 15

Une **clôture de développement backend local** est possible si les dernières sorties de tests ont un code 0 et les comptes ci-après sont enregistrés dans `docs/certification/PHASE14_CLOTURE_v0.49.13_TEST_EVIDENCE.txt`.

La Phase 15 peut être entamée à partir de ce checkpoint sans requalifier les preuves pédagogiques comme notes officielles. Les essais machine, production, providers et certification globale relèvent des phases déjà figées (22–25). Ne jamais appeler ce résultat une certification production.

# EduNova v0.49.9 — Phase 14 : identité institutionnelle et provenance des preuves pédagogiques

**Checkpoint d'entrée** : `EduNova_v0.49.8_RC_PHASE14_ASSESSMENT_EVIDENCE_INTEGRITY.zip`

**SHA-256 source vérifié** : `ebf380e102ddecc3da1f5868c877be9ba3ca97b653dfd5d315a8fe0f94e80d4a`.

**Périmètre** : consolidation incrémentale de l'intelligence pédagogique, sur les modules existants. La roadmap et les phases 0–13 sont maintenues ; Phase 14 toujours en cours.

## Changements livrés dans le code

1. **Identité canonique étudiant / compte** : les résultats publiés sont toujours contrôlés par institution, offre, cours, appartenance au groupe actif et unicité par compte. Désormais, si deux comptes distincts pointent vers le même `student_id` à l'intérieur du groupe de résultats admissibles, leurs résultats sont écartés ensemble. Une migration ou fusion SIS incohérente ne doit pas gonfler l'effectif réellement évalué. L'identité d'un établissement étranger n'entre pas dans cette détection.
2. **Hachage de provenance sensible aux changements** : le SHA-256 agrégé du signal de cours inclut maintenant les champs de preuve du résultat publié (identifiant d'enregistrement, étudiant, compte, inscription, empreinte de publication, pourcentage, verdict) et ceux de présence (session, étudiant, statut, revue, risque). Un changement de note avec un `evidence_hash` amont obsolète, ou une revue de présence nouvellement contestée, modifie désormais l'empreinte agrégée. Ces identifiants demeurent **internes au calcul** et ne sont jamais retournés tels quels.
3. **Assiduité : grille de couverture vérifiée** : la complétude exige aussi un couple distinct `(session clôturée, étudiant actif)` pour chaque présence attendue, en plus des contrôles de statut et de revue. La contrainte de base couvre déjà l'unicité ; ce contrôle protège également la projection analytique en lecture seule contre une source incohérente.
4. **Tentatives notées sans soumission** : un `AttemptRow.state='graded'` sans `submitted_at` ne peut plus contribuer ni au rapport par objectif, ni aux tendances / erreurs collectives. La tentative la plus récente reste sélectionnée *avant* cette vérification : on n'exhume pas une ancienne reprise valide pour masquer une plus récente incohérente.
5. **Décisions inchangées** : aucun diagnostic individuel, aucune modification du gradebook, aucune mutation du jury ou de l'inscription ; agrégats de moins de trois évalués supprimés au niveau des rapports exposés.

## Scénarios adversariaux ajoutés (6)

- Comptes universitaires distincts pointant vers le même `student_id` ; exclusion conservatrice des deux notes, sans doublage du groupe.
- Collision du même identifiant dans une institution différente : pas de mélange inter-universités.
- Modification rétroactive du pourcentage d'un résultat publié malgré son empreinte source inchangée : nouvelle empreinte de sortie.
- Revue de présence passée de `clear` à `needs_review` : taux non affiché et empreinte modifiée.
- Reprise la plus récente indiquée notée mais sans date de soumission : les anciennes copies ne réapparaissent pas.
- Ancienne copie irrégulière (sans date de soumission) ne supplante pas une copie postérieure valide.

Tests ciblés exécutés sur les véritables tables ORM en SQLite local avec conflits multi-institutions ; les tests préexistants couvrent également RBAC, contrôle de groupe actif et confidentialité des petits effectifs.

## Périmètre de validation et limites

- Les résultats exacts (baseline, nouvelle suite complète, suite ciblée, audit structurel et compilation Python) sont consignés sous `docs/certification/PHASE14_IDENTITY_PROVENANCE_v0.49.9_TEST_EVIDENCE.txt`.
- **Aucune migration SQL ajoutée**. Le schéma existant, jusqu'à `0082`, est inchangé ; aucune table métier n'a été reconstruite.
- **Pas de garantie d'immutabilité** : l'empreinte atteste une projection déterministe à un instant donné, pas une signature qualifiée, un registre append-only, ni une preuve légale. Les comparaisons dans le temps nécessitent la conservation fiable des empreintes antérieures.
- Des fusions de comptes réellement voulues devront être normalisées par les services SIS compétents. En cas d'ambiguïté, exclusion plutôt qu'attribution arbitraire.
- Les modèles de corrections détaillées sont encore dépendants des catalogues courants (limitations déjà identifiées dans v0.49.8) ; pas de nouveau modèle psychométrique.
- **Flutter/Dart, PostgreSQL réel, Redis, workers, stockage objet, fournisseurs tiers, appareils et signatures qualifiées NON CERTIFIÉS** par cette étape de développement backend/SQLite. La compilation Python n'est pas une compilation Flutter.

**Fichiers mis à jour** : `services/api/app/modules/pedagogical_intelligence/infrastructure.py`, `services/api/tests/test_phase14_pedagogical_intelligence.py`, `services/api/app/version.py`, `apps/{mobile,admin}/pubspec.yaml`, `README.md`, le présent rapport et l'attestation d'exécution.

**Statut** : EduNova v0.49.9, Phase 14 approfondie, non close ; passage à Phase 15 non autorisé par ce checkpoint.

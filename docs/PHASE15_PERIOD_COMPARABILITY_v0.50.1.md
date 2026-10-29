# EduNova — Phase 15 / Comparabilité gouvernée v0.50.1

## Décision de conception

Réutilisation de `institutional_analytics` (Lot 27 et v0.50.0). Aucun nouveau module parallèle.

### API ajoutée

`GET /v1/institutional-analytics/institutions/{iid}/intelligence/period-comparison?previous_period_id=...&current_period_id=...&academic_unit_id=...`

- Authentification et RBAC identiques à `decision-brief` : OWNER, RECTOR, ADMIN, ACADEMIC_ADMIN, AUDITOR, FACULTY_ADMIN dans sa sous-arborescence uniquement. Ni étudiant ni enseignant.
- Deux périodes différentes, actives, du même type, ordonnées et non chevauchantes dans la même université ; même périmètre institutionnel ou même unité académique dans les deux périodes.
- Résultats en **points de pourcentage**, pas en pourcentage de variation relative.
- Deux populations d'au moins **5 étudiants distincts** chacune et **aucun étudiant présent dans les deux populations**. Les chevauchements sont calculés côté SQL et ne sont jamais exposés.
- Une métrique n'est publiée que si les deux côtés sont individuellement publiables par `decision_brief`, avec contrat source et définition identiques. Sinon résultat et delta `null` ; pas de fabrication de tendance.
- Aucun compte étudiant, note individuelle, nom, identifiant d'apprenant ou dénominateur source dans la réponse comparative.
- Pas de modification des inscriptions, grades, délibérations ou décisions ; lecture seule, audit métier si configuré.

Ce mécanisme **ne prétend pas offrir la confidentialité différentielle** : des requêtes répétées sur des sous-groupes recouvrants restent une préoccupation. Il s'agit d'un premier garde-fou conservateur contre les comparaisons directement déductives. Le développement de garde-fous inter-requêtes cohérents reste ouvert pour la Phase 15 / Phase 20.

### Correction des indicateurs sous-jacents

- Dans la projection `governed=True`, les opportunités de soumission sont calculées sur les étudiants **uniques, actifs et locaux au tenant**, plutôt que sur des inscriptions brutes non filtrées par université ; cela protège les taux contre la corruption inter-tenant.
- Les populations servant au contrôle de diffusion doivent provenir de cohortes actives et du même tenant et, si une période est demandée, avoir la même période que la requête.
- Une `assignments.submission_rate` ne devient publiable que si au moins trois **auteurs de soumissions distincts** l'alimentent, même lorsque des dizaines de soumissions proviennent d'une seule personne.
- Les indicateurs sensibles de présence et de résultats échouent désormais en confidentialité **fail-closed** si leurs métadonnées de contributeurs manquent.
- Les cinq indicateurs de `decision_brief` exposent un identifiant stable de contrat de source ; le changement d'une définition interdira la comparaison avant revue.

### Sources de données

- Séances et syllabus institutionnels, présences de séances closes et revues (`clear`), devoirs publiés et soumissions d'inscrits actifs, résultats validés de gradebooks publiés.
- Aucun accès aux conversations privées, dossiers individuels Student Success, réponses de tutor ou données privées hors des contextes institutionnels autorisés.

### Non-couverture et certification

Le produit conserve la Phase 15 **ouverte**. Ce checkpoint n'atteste pas : anonymisation formelle, réconciliation automatique de sources historiques, migration PostgreSQL réelle, Redis réel, compilation Flutter, certification appareil, provider externe, décision du jury.

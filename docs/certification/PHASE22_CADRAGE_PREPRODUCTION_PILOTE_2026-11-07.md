# EduNova — Phase 22 : préproduction et pilote contrôlé

**Démarrage :** 7 novembre 2026  
**Base :** Phase 21 fusionnée, commit `f82ef519058f242ef617b40c7dce4446f3da1575`  
**Branche :** `codex/phase22-controlled-pilot-readiness`  
**Statut initial :** EN COURS

## Objectif

Transformer la certification fonctionnelle de la Phase 21 en une capacité de pilote contrôlé, reproductible et exploitable sans exposer de secrets ni effectuer de paiement réel.

## Lots de travail

| Lot | Résultat attendu |
| --- | --- |
| 22.A — configuration | Validation fail-closed des variables, secrets, CORS, stockage privé, IA et paiement sandbox |
| 22.B — déploiement | Composition préproduction durcie, readiness joignable en loopback, migration et rollback testables |
| 22.C — continuité | Sauvegarde PostgreSQL et objets, vérification des hashes, restauration éphémère et preuve d'intégrité |
| 22.D — observabilité | Santé, métriques, corrélation, redaction des secrets et procédure d'incident pilote |
| 22.E — client pilote | APK traçable, configuration API HTTPS, manifeste, procédure d'installation et limites de signature |
| 22.F — certification | CI dédiée, preuves, matrice GO/NO-GO et rapport final avec SHA exact |

## Frontières d'autorité

La phase prépare techniquement la signature officielle, les contrats Mobile Money, les appareils physiques et les comptes stores. Ces éléments ne seront déclarés vérifiés qu'après fourniture et validation par le propriétaire. Aucune transaction réelle, aucun déploiement production et aucun secret réel ne sont autorisés dans GitHub.

## Critères de sortie

- environnement de préproduction invalide refusé avant démarrage ;
- migrations, démarrage, readiness et rollback reproductibles ;
- restauration PostgreSQL prouvée sur base éphémère avec invariants ;
- données privées et secrets absents des journaux et artefacts ;
- build Android pilote traçable vers un commit ;
- tous les contrôles Phase 22 et non-régressions pertinents verts ;
- limites externes consignées sans faux PASS.

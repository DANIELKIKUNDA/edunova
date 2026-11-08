# Phase 17 v0.52.2 — Protection du propriétaire et CI dédiée

- Backend : une attribution du rôle `owner` exige que l’acteur soit déjà `owner`, même si une permission `platform.roles.manage` était ajoutée ultérieurement à un autre rôle.
- Backend : un membre propriétaire ne peut être modifié ni désactivé par un autre rôle, indépendamment des permissions additionnelles.
- Tests : nouveau test HTTP d’isolation de propriétaire, plus tests existants de gouvernance et contrat Flutter. Résultat exécuté : 11/11 PASS.
- Flutter admin : avertissement explicite lors de l’attribution du rôle propriétaire ; version 0.52.2+17002.
- GitHub Actions : workflow dédié Phase 17 avec backend et analyse/tests/build Web Flutter admin. YAML analysé localement.
- API : version 0.52.2.

## Limites
SDK Flutter absent dans cet environnement ; aucune compilation Flutter revendiquée. GitHub Actions non exécuté à distance (dépôt inaccessible au connecteur). Phase 17 toujours en cours : gouvernance institutionnelle et support central à implémenter.

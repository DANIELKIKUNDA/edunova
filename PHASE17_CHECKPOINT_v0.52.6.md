# EduNova v0.52.6 — Gouvernance centrale : indicateurs et journal

## Code intégré
- API `GET /v1/platform/institutions/statistics` : agrégats des établissements, permission `platform.analytics.read`.
- API `GET /v1/platform/audit/events` : journal paginé et filtré des décisions centrales, permission `platform.audit.read`.
- La liste d'audit ne renvoie ni métadonnées libres ni événements étudiants/paiements.
- Flutter admin : cartes d'indicateurs et liste d'événements affichées selon permissions.
- Tests SQL SQLite sur agrégats, pagination, filtrage et absence de données privées.

## Vérifications exécutées
- 10/10 tests ciblés réussis, y compris 2 nouveaux tests SQL.
- Compilation syntaxique Python réussie.
- Flutter SDK absent : analyse et compilation Flutter non effectuées.
- Pas de push GitHub Actions, compte connecté mais aucun dépôt autorisé.

## À compléter avant clôture intégrale de la Phase 17
- Affectations des administrateurs institutionnels (backend + Flutter), avec gestion d'invitations et révocation.
- Support central avec autorisations et flux de tickets, UI opérationnelle.
- Tests d'intégration API, suite de régression backend complète, compilation et tests Flutter.
- Certification finale sur la machine de l'utilisateur.

**Statut : Phase 17 EN COURS.** Ce checkpoint n'est pas une déclaration de clôture.

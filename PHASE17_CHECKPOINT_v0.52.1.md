# EduNova v0.52.1 — Phase 17 lot 2 : gestion effective des accès

- Flutter Studio : création/affectation des membres plateforme, modification des rôles et désactivation confirmée.
- API existante utilisée sans élargissement des privilèges : `PUT /v1/platform/members/{account_id}`, `POST .../deactivate`.
- Contrôle `platform.roles.manage` conservé côté serveur; UI affichée seulement aux comptes autorisés.
- Versions optimistes `expected_version` et gestion HTTP 409 avec rechargement.
- Les données privées des étudiants ne sont ni exposées ni manipulées.
- Compilation Flutter SDK non disponible localement : validation Flutter réelle reportée à la certification sur machine.
- Phase 17 reste en cours (gouvernance institutions, activation/suspension, support, audit).

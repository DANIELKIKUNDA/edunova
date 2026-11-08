# EduNova v0.52.0 — Phase 17, lot 1

## Travail implémenté
- Interface Flutter administration : récupération de la liste des membres de gouvernance uniquement pour les comptes possédant `platform.roles.manage`.
- Affichage des rôles, états actif/inactif, identifiants et versions de concurrence dans le centre de contrôle.
- Aucune donnée privée d’étudiant n’est affichée. Les autorisations restent imposées côté API.
- Backend : réutilisation du RBAC existant et des endpoints `/v1/platform/me`, `/dashboard`, `/members`.
- Version API : 0.52.0.

## Statut
Phase 17 commencée, non clôturée. Ce lot est une intégration frontend réelle au backend existant, pas une simulation.
Flutter SDK et GitHub Actions non disponibles dans cet environnement; compilation Flutter à faire sur la machine de certification.

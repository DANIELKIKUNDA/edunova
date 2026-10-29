# EduNova v0.53.1 — Phase 18 lot 2

## Implémenté
- GET `/v1/commerce/combined-access?institution_id=...`, authentifié.
- Premium calculé depuis l’abonnement réel de l’utilisateur.
- Campus calculé depuis l’affiliation active STUDENT, l’état réel de l’établissement et la licence en vigueur.
- Sièges Campus : modèle existant d’allocation **implicite** par membre étudiant actif, seulement si l’effectif total ne dépasse pas la capacité. Aucune table d’affectation individuelle n’existe actuellement.
- Pas de changement des permissions d’accès aux ressources Campus : cette API est un état de présentation, pas une source d’autorisation.
- Les droits Premium ne sont jamais retirés par une suspension Campus.

## Reste à faire
- Intégration de cette API dans les écrans Flutter et leurs états hors-ligne.
- Tests d’intégration réels multi-tenant et validation Flutter sur machine utilisateur.

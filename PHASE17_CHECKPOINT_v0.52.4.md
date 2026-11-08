# EduNova 0.52.4 — Annuaire central des établissements

## Implémentation
- Endpoint `GET /v1/platform/institutions/directory` : RBAC `platform.institutions.read`, pagination bornée (1–100), offset, filtre de statut et recherche nom/slug insensible à la casse.
- Projection minimale : identifiant, nom, slug, pays, ville, statut et version. Aucun dossier étudiant, paiement ou adhésion institutionnelle exposé.
- Flutter administration : liste des 50 premiers établissements, navigation vers le contrôle administratif; version du contrôle existant conservée pour l'optimistic locking.
- GitHub Actions : test de l'annuaire inclus dans le job de gouvernance.

## Validation locale
- 7 tests ciblés réussis (annuaire, contrôle institutionnel, protection propriétaire, contrat Flutter).
- Flutter SDK et GitHub Actions non exécutés dans cet environnement.
- L'annuaire Flutter affiche actuellement la première page uniquement; pagination interactive à compléter.
- Phase 17 en cours; certification réelle sur la machine du propriétaire.

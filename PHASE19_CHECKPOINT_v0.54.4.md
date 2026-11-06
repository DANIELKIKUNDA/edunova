# EduNova v0.54.4 — Phase 19, protection de la reconstruction canonique

## Modifications
- Lors d'un `reset_required`, le snapshot distant est téléchargé et validé **avant** `prepareCanonicalReset`. Un snapshot invalide ou une requête réseau échouée ne déclenche donc pas l'effacement préparatoire des données synchronisées locales.
- Les deltas doivent désormais présenter des séquences serveur strictement croissantes; les lots inversés ou dupliqués sont rejetés avant écriture.
- Deux tests Flutter de non-régression ajoutés pour ces scénarios.

## Vérifications
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*` : 17 réussis.
- Flutter SDK non disponible ici : tests Flutter ajoutés mais non exécutés.
- Phase 19 toujours en cours; une transaction locale atomique pour l'application complète d'un snapshot reste une amélioration distincte.

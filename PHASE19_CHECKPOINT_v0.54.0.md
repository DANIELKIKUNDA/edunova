# EduNova v0.54.0 — Phase 19, consolidation synchronisation (lot 1)

Base : v0.53.16, archive complète conservée.

## Correctifs Flutter
- Vérification stricte des réponses `push` : rejette réponse partielle, identifiant inconnu ou dupliqué avant de marquer les mutations locales comme appliquées.
- Rejette les dispositions serveur inconnues et les conflits sans enregistrement canonique ; aucune progression de pull/ack sur ces anomalies.
- Vérification `mounted` avant `setState` dans la page de synchronisation après une réponse réseau asynchrone.
- Trois tests Flutter de non-régression ajoutés (`sync_push_integrity_test.dart`).

## Preuves
- Backend : `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : **17 passed**.
- Contrat statique des 4 protections : présent.
- SDK Flutter/Dart absent : tests Dart ajoutés mais **non exécutés**. Aucun succès Flutter revendiqué.
- Pas de certification globale Phase 19 : les autres parcours UX/offline restent à examiner.

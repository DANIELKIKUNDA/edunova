# EduNova Phase 19 — checkpoint v0.54.8

## Correction effective

Le gestionnaire `RunCloudSync` ne réécrit plus son curseur local en cas d'erreur réseau après application transactionnelle d'une page. L'ancienne gestion d'erreur utilisait un curseur mémorisé en début de run, susceptible d'être obsolète lors d'un échec d'acknowledgement. Le dépôt Drift enregistre maintenant uniquement `lastError` et `updatedAt`, sans modifier `serverCursor`, `retainedFloor` ou les données synchronisées.

Le contrat `CloudSyncLocalRepository` fournit `recordSyncError`; une implémentation par défaut conserve la compatibilité des doubles de test. Un test de régression Flutter vérifie le maintien du curseur après échec d'acknowledgement.

## Vérifications

- Backend sync : 17/17 PASS (`PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*`).
- Flutter : test ajouté, non exécuté (SDK Flutter absent).
- Phase 19 : non certifiée; audit UX/offline transversal et régression Flutter restent nécessaires.

# EduNova v0.55.1 — Phase 19 : protection des modifications hors connexion

## Correctifs implémentés
- `DriftCloudSyncRepository.applyRemoteRecord` : si une mutation `pending` existe pour le même compte, type et identifiant, la version canonique est mémorisée sans écraser ni supprimer la projection locale non envoyée.
- `prepareCanonicalReset` : conservation des versions serveur des entités ayant des mutations `pending` ou `conflict`, au lieu de supprimer toutes les versions.
- Les conflits explicites continuent à appliquer l’état canonique lors du traitement du conflit.

## Contrôles
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : 17 tests réussis.
- Régression backend complète lancée mais non terminée dans la limite d'exécution : aucune conclusion de réussite globale.
- SDK Flutter/Dart absent : aucune compilation ni exécution des tests Flutter possible ici.

## Décision
**Phase 19 : développement renforcé, clôture/certification non acquise.** Nécessite tests Flutter et tests de parcours hors connexion sur émulateur ou appareil, ainsi qu’une régression générale complète. La Phase 23 reste dédiée à la certification sur appareils réels.

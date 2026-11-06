# EduNova v0.54.1 — Phase 19, intégrité de synchronisation (lot 2)

- Prévalidation de toutes les dispositions du push avant mutation de l’outbox : évite l’acquittement partiel si une réponse contient une disposition invalide ou un conflit sans canonique.
- Validation des curseurs de pull : refuse un curseur régressif et une pagination sans progression.
- Quatre nouveaux tests Flutter ajoutés pour ces scénarios ; non exécutés (SDK Flutter/Dart indisponible).
- Backend : `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : **17 passed**.
- Phase 19 toujours en cours : certification Flutter et autres parcours hors-ligne restent ouverts.

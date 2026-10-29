# EduNova Phase 19 — v0.54.5 — Atomicité locale des pages synchronisées

## Changements réalisés
- Nouvelle opération `applyCanonicalPage` dans le contrat du dépôt local.
- Implémentation Drift transactionnelle : reset canonique éventuel, application des projections et avancement du curseur sont exécutés dans une même transaction SQLite.
- `RunCloudSync` utilise cette opération pour le bootstrap initial, les pages delta et la reconstruction après compaction. Un échec de projection annule la page complète au niveau Drift.
- Adaptation des doubles de tests Flutter aux nouvelles signatures.

## Vérifications effectuées
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : 17/17 PASS.
- Flutter SDK absent : compilation et tests Flutter non exécutés.

## Limitations et travaux de clôture
- Le traitement de la file d'envoi (push) conserve plusieurs écritures locales successives ; une transaction unique pour l'ensemble des résultats reste à auditer.
- Les scénarios d'interruption/reprise réseau, l'isolation des comptes et les parcours UX/offline globaux nécessitent des tests Flutter.
- Une transaction SQLite assure le rollback des projections locales, pas l'atomicité distribuée entre le serveur et le client.
- La phase 19 ne peut pas être certifiée complète sur la base de ce checkpoint.

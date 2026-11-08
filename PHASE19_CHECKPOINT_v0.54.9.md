# EduNova v0.54.9 — Phase 19 — Push canonical identity validation

## Changements réels
- Validation avant toute écriture de l'identité (type et identifiant) des enregistrements canoniques associés aux résultats de push.
- Rejet des versions inférieures à 1 et des séquences négatives.
- Double garde dans RunCloudSync et DriftCloudSyncRepository, pour les appels directs au dépôt.
- Trois tests Flutter de non-corruption ajoutés dans `sync_push_integrity_test.dart`.

## Vérifications
- Backend `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*` : 17 passed.
- Flutter : non exécuté, SDK indisponible dans cet environnement.
- Régression générale : non exécutée.

## État
Phase 19 en cours : la certification Flutter, les parcours offline/UX transversaux et l'audit d'isolation de données restent nécessaires. Ne pas déclarer clôturée.

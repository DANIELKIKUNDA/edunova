# EduNova v0.55.2 — Phase 19 : intégrité monotone du registre canonique

## Modification de code
- `DriftCloudSyncRepository.applyRemoteRecord` refuse d'appliquer une projection canonique si la version **ou** la séquence serveur n'est pas strictement plus récente que celle déjà mémorisée pour le compte et l'entité. Cela protège notamment contre les réponses réseau retardées.
- `_saveVersion` refuse également les écritures régressives provenant des confirmations d'envoi et de la résolution des conflits. Ce garde-fou est centralisé afin de protéger tous ses appelants.
- Les protections v0.55.1 des modifications locales `pending` et des versions lors du reset sont conservées.

## Vérifications réellement exécutées
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : **17 réussis**.
- Régression backend générale : **interrompue avant son terme** ; progression partielle consignée dans `PHASE19_BACKEND_REGRESSION_v0.55.2.log`. Aucun PASS global revendiqué.
- SDK Flutter/Dart indisponible dans l'environnement : tests Flutter et compilation non exécutés.

## Réserves
- L'isolation physique des projections SQLite entre comptes doit être évaluée transversalement : les tables locales métier ne portent pas toutes un `accountId`.
- La compilation Flutter, les tests d'intégration des parcours hors connexion et les vérifications sur appareil ne sont pas certifiés.
- **La phase 19 ne peut pas être déclarée certifiée ou totalement achevée.** Phase 23 : certification sur appareils réels.

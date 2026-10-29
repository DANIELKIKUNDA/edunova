# EduNova v0.57.8 — Phase 19 / Point C : validation de sécurité

## Correction réellement effectuée
- Neuf repositories de données privées utilisent désormais `assertOwned()` au lieu du contrôle permissif `assertReadable()`.
- Les flux protégés par `LocalAccountAccess.protect()` exigent désormais un propriétaire authentifié par défaut (`owned = true`).
- Le catalogue de la bibliothèque conserve son accès public contrôlé; les suivis privés y ont déjà leur contrôle `assertOwned()`.

## Vérifications exécutées
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : **17 passed**.
- `python -m compileall -q services/api` : **réussi**.
- Inspection statique : les appels `assertReadable()` restants dans les repositories concernés se trouvent dans le repository de bibliothèque, qui combine catalogue public et suivis privés.

## Réserves / critères de clôture
- Flutter/Dart SDK absent : aucune compilation, analyse Dart ni exécution de tests Flutter. Les changements Dart ne sont **pas certifiés**.
- Les protections `assertOwned()` peuvent restreindre certains parcours anonymes offline-first auparavant permis. Vérifier les parcours produit et prévoir une migration/attribution explicite des données historiques.
- Régression backend complète non terminée lors de cette intervention.
- Aucun essai sur appareil réel : réservé à la phase 23.

**Décision : la phase 19 ne peut pas être déclarée certifiée.**

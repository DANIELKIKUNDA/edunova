# LOT 7 — Preuves ChatGPT v0.8.1

## Backend
- `pytest -q` : **181/181 PASS**.
- `python -m compileall -q app tests` : PASS.
- audit `TODO|FIXME|NotImplementedError` dans `app` et `tests` : PASS.

## Durcissements vérifiés
- idempotence et conflits optimistes ;
- snapshot/bootstrap et deltas par curseur ;
- accusé de réception par appareil ;
- révocation d’appareil ;
- compaction sûre et `reset_required` pour client trop ancien ;
- isolation des comptes ;
- validation stricte des payloads et rejet des champs privés ;
- catalogue anonyme/freemium ;
- ETag stable et pagination par curseur opaque ;
- jetons de livraison liés compte+ressource+expiration ;
- `course_follow` synchronisable et strictement validé.

## Flutter
Code Drift v13 et UI approfondie préparés. Le statut reste `OPEN-machine` tant que `build_runner`, `flutter analyze`, `flutter test` et les builds réels n’ont pas été exécutés.

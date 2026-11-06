# LOT 13 — Acceptation finale v0.14.1

## Portée certifiable dans l’environnement ChatGPT
- suite backend complète ;
- compilation Python ;
- tests Content Factory ;
- provenance et intégrité SHA-256 ;
- garde des assertions numériques ;
- détection de quasi-doublons ;
- paquet de revue source ↔ artefact ;
- interdiction de publication automatique ;
- annulation des runs en attente ;
- audit statique du LOT 13.

## OPEN-machine
- `flutter pub get`, `flutter analyze`, `flutter test`, `flutter build web` ;
- revue responsive réelle desktop/tablette/mobile ;
- PostgreSQL réel sous concurrence multi-worker ;
- endurance/reprise worker supervisé ;
- corpus massif et mesure SLA ;
- fournisseurs IA externes réels et leurs budgets/circuit-breakers.

Aucun de ces points OPEN-machine ne doit être déclaré PASS sans exécution réelle.

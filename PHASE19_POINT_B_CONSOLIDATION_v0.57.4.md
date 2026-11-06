# EduNova v0.57.4 — Phase 19, point B : consolidation des parcours

## Base
Archive v0.57.3. Modifications ciblées dans `calendar_page.dart` et `offline_resource_tile.dart`.

## Corrections
- Calendrier : enregistrement effectué à l'intérieur des dialogues ; les champs restent saisis si SQLite échoue, avec possibilité de réessayer sans tout ressaisir.
- Calendrier : prévention des doubles validations, indicateur de progression, désactivation des actions durant la sauvegarde.
- Horaires : validation stricte HH:MM ; saisie incorrecte non remplacée silencieusement par une heure par défaut.
- Téléchargements hors ligne : erreurs d'épinglage interceptées et présentées à l'utilisateur ; prévention des actions concurrentes sur le bouton.

## Vérification
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*` : **17 passed in 9.39s**.
- Flutter/Dart non installés : compilation et tests Flutter **non exécutés**. Les tests backend ne valident pas les modifications Dart.

## État
Le point B est consolidé pour les corrections identifiées, mais la revue complète des transitions réseau et de la lecture hors ligne reste une réserve d'audit. Aucune certification Flutter ou sur appareil réel n'est revendiquée. Le point C doit compiler/tester Flutter avant clôture définitive de la Phase 19.

# EduNova v0.57.2 — Phase 19 / Point B — Quiz et flashcards

## Modifications
- Quiz : verrouillage des actions pendant la sauvegarde pour éviter les doubles clics, affichage des erreurs de sauvegarde et de finalisation, reprise de session avec action Réessayer en cas d’échec.
- Flashcards : verrouillage des quatre actions de notation pendant la sauvegarde et message d’erreur en cas d’échec, sans avancer la carte.

## Vérifications
- Tests backend sync : 17/17 PASS (14,96 s).
- SDK Flutter/Dart absent : compilation et tests widget NON EXÉCUTÉS.
- La persistance atomique de toutes les écritures d’une réponse de quiz n’est pas garantie par ces changements UI; à auditer dans la couche repository.
- Lecture offline, calendrier, synchronisation et parcours Flutter restent à auditer avant clôture du point B.

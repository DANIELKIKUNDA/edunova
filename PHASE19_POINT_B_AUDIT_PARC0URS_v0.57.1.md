# EduNova v0.57.1 — Phase 19, point B : audit des parcours Flutter (première consolidation)

## Base
Archive source : `EduNova_v0.57.0_PHASE19_POINT_A_CONSOLIDATION.zip`.

## Parcours inspectés
- Authentification : écran de connexion, retour au bootstrap et messages d'échec.
- Bibliothèque : chargement de manifeste, affichage des ressources et téléchargement d'un cours.
- Stockage hors ligne : ressources, épinglage, nettoyage et confirmation de suppression.
- Synchronisation : état cloud, appareils, révocation, diagnostics et résolution des conflits.
- Présence des écrans quiz, flashcards et calendrier vérifiée ; audit fonctionnel détaillé restant.

## Corrections effectives
1. `library_course_page.dart` : bouton Télécharger désactivé sans manifeste valide ; protection contre les doubles déclenchements ; indicateur d'activité ; état réinitialisé en fin d'opération.
2. `library_course_page.dart` : message d'échec de chargement et action Réessayer ; effacement de l'erreur au nouveau chargement.
3. `sync_status_page.dart` : révocation d'appareil protégée contre les déclenchements simultanés ; erreur affichée à l'utilisateur ; retour d'état garanti après l'opération.

## Vérifications
- Backend : `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*` : **17/17 PASS**.
- SDK Flutter/Dart : indisponible, compilation et tests Flutter non exécutés.
- Inspection statique ciblée : effectuée ; ne remplace pas la compilation.

## Statut
**Point B EN COURS**, non certifié. Restent l'audit détaillé des parcours lecture hors ligne, quiz, flashcards, calendrier et les régressions Flutter ; la certification générale relève du point C.

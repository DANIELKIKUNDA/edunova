# LOT 7 — Certification machine v0.8.1

## Flutter/Drift
1. `flutter pub get`
2. `dart run build_runner build --delete-conflicting-outputs`
3. Vérifier migration Drift v12 -> v13 (`LocalLibraryCourseFollows`).
4. `flutter analyze`
5. `flutter test`
6. Build Android, Web et Windows.

## Scénarios multi-appareils obligatoires
- appareil A modifie calendrier, B reçoit la modification ;
- conflit simultané : aucun overwrite silencieux ;
- résolution cloud puis locale ;
- révocation d’un appareil : push/pull refusés ;
- appareil longtemps absent : `reset_required` puis bootstrap canonique ;
- cours suivi sur A apparaît suivi sur B ;
- PDF/photo personnel n’apparaît jamais sur B ;
- page Santé sync affiche pending/conflits/rejets ;
- catalogue reste disponible hors connexion depuis le cache ;
- version/changelog visibles dans la fiche d’un cours.

## Backend production
Appliquer migrations 0001 -> 0005 dans l’ordre et exécuter la suite backend complète avant déploiement.

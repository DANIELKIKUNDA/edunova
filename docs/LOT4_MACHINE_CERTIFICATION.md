# LOT 4 — Certification machine obligatoire

## A. Génération / analyse Flutter

1. `flutter pub get`
2. `dart run build_runner build --delete-conflicting-outputs`
3. `flutter analyze`
4. `flutter test`

Attendu : **0 erreur d’analyse et tous les tests PASS**.

## B. Migration Drift

- installer une base v5 contenant horaire/échéances/plans ;
- lancer l’application v6 ;
- vérifier la migration v5 → v6 sans perte ;
- vérifier les nouvelles tables : disponibilité, périmètres, dette, révisions, blocs, sessions, actions ;
- vérifier les nouvelles colonnes de préférences.

## C. Planning offline

En mode avion :
- générer un plan à partir de données déjà locales ;
- respecter les plages disponibles ;
- vérifier pauses et max travail continu ;
- terminer un bloc ;
- reporter un bloc ;
- épingler un bloc ;
- fermer/réouvrir l’application ;
- confirmer la persistance de toutes les actions.

## D. Horaire → disponibilités

- importer un horaire OCR ;
- valider les cours ;
- définir une plage préférée ;
- vérifier que les cours sont soustraits des créneaux libres ;
- vérifier les conflits.

## E. Évaluations

- définir une interrogation avec chapitres concernés ;
- calculer charge et faisabilité ;
- déplacer la date ;
- vérifier replanification ;
- vérifier conservation des blocs terminés/épinglés ;
- tester surcharge avec temps insuffisant.

## F. Notifications

À certifier avec l’adaptateur de notifications locales de la cible :
- permissions ;
- heures calmes ;
- plafond quotidien ;
- déplacement d’échéance ;
- annulation des rappels obsolètes ;
- Android ; iOS/PWA selon capacités de la plateforme.

## G. Builds

- Android debug/release candidate ;
- Windows debug ;
- Web/PWA ;
- iOS via environnement macOS lorsque la cible native est ouverte.

**Tant que cette matrice n’est pas verte, LOT 4 reste `READY_FOR_MACHINE_CERTIFICATION`, pas `CLOSED`.**

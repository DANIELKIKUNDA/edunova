# EduNova v0.56.5 — Phase 19 / Point A : bibliothèque publique et suivis privés

## Modifications
- `DriftLibraryRepository.watchCourses`: contrôle d'accès avant abonnement et avant chaque émission; refuse de publier les états `followed` lorsqu'un propriétaire valide et authentifié ne peut pas être confirmé.
- `DriftLibraryRepository.setCourseFollowed`: requiert explicitement un propriétaire authentifié, y compris sur une installation initialement anonyme.
- `LocalAccountAccess.assertOwned`: nouvelle exigence pour les projections privées; refuse les données privées orphelines.

## Limites et risques non résolus
- Le flux du catalogue public est actuellement refusé si une installation historique contient des suivis privés sans propriétaire identifiable : choix fail-closed, au prix d'une disponibilité réduite du catalogue sur ces installations.
- Le flux Drift peut être invalidé lors d'une déconnexion sans modification SQL; l'émission déjà livrée au client n'est pas effacée par cette seule garde. Un invalidateur de session centralisé reste à vérifier.
- Autres repositories, téléchargements et opérations asynchrones en cours non certifiés exhaustivement.
- Tests Flutter et compilation impossibles ici en l'absence de SDK Flutter/Dart. Aucun PASS Flutter revendiqué.

## Vérifications
- Tests backend de synchronisation : 17/17 PASS (11.03 s), avant finalisation de cette modification Dart.
- Contrôle de l'archive ZIP et SHA-256 à la livraison.

## Statut
Point A non certifié; correction ciblée de confidentialité de la bibliothèque, revue Flutter nécessaire.

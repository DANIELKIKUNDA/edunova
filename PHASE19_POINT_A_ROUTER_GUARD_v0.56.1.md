# EduNova v0.56.1 — Phase 19, point A : garde globale du routeur

## Changements
- `GoRouter.redirect` vérifie la session persistante avant toute construction d'une route métier, y compris les liens profonds.
- En l'absence de session, le routeur renvoie vers `/bootstrap`, où sont inspectées les données SQLite historiques et les ressources hors connexion.
- L'expérience anonyme offline-first reste accessible uniquement après validation de ce bootstrap et en l'absence de propriétaire durable.
- Une installation déjà attribuée à un étudiant ne bénéficie jamais de cette exception après déconnexion.
- Toute erreur de lecture du stockage sécurisé échoue en mode fermé et renvoie vers `/login`.

## Limites et réserve
- La garde globale réduit les accès directs mais ne remplace pas l'autorisation au niveau des repositories métier.
- Le drapeau de validation anonyme est conservé uniquement en mémoire du processus ; il ne constitue pas une preuve d'authentification.
- SDK Flutter/Dart indisponible ici : compilation et tests Flutter non exécutés. L'intégration reste à certifier.
- Point A : code renforcé, certification finale non prononcée.

## Vérification
- Tests backend `test_sync_lot7.py` : 17 réussis.

# EduNova v0.57.6 — Phase 19, point B — Vérification de disponibilité hors connexion

## Correction intégrée

L'écran `OfflineStoragePage` ne se fie plus uniquement au drapeau SQLite `ready`. Il consulte `OfflineResourceStore.finalUri(resourceId)` et vérifie la concordance avec `localUri` avant d'afficher « Disponible hors connexion ». Si le fichier est absent ou inaccessible, il affiche un avertissement et invite à le télécharger à nouveau. Le contrôle est mis en cache via un `FutureProvider.family` Riverpod afin d'éviter les lectures répétées à chaque reconstruction de l'interface. L'entrée du cache de vérification est invalidée après suppression du fichier.

## Vérifications

- Tests backend sync : 17/17 réussis (`PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*`).
- SDK Flutter/Dart : indisponible dans cet environnement ; compilation et tests Flutter non exécutés.
- Le contrôle vérifie la présence de la ressource, **pas** l'ouverture réelle ni l'intégrité cryptographique du contenu. Ces vérifications restent à couvrir lors de la validation technique C et sur appareils en phase 23.
- Le point B est consolidé mais ne doit pas être déclaré certifié sur appareil.

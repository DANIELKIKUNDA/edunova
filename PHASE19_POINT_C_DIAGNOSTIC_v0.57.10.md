# EduNova — Phase 19 / Point C — Diagnostic de certification v0.57.10

Date : 23 octobre 2026

## Contrôles exécutés
- Suite de synchronisation backend : **17/17 PASS** (`PYTHONPATH=services/api pytest -q services/api/tests/test_sync*`).
- Collecte de la suite backend : **1 169 tests collectés** en 14,88 s.
- Régression complète : progression à **6 % (~75 tests)** avant interruption du délai d'exécution ; **aucun PASS global revendiqué**.
- Flutter et Dart : **non installés** dans l'environnement ; ni `flutter analyze`, ni `flutter test`, ni build exécutables ici.

## Revue de sécurité du code
- `LocalAccountAccess.assertReadable()` accepte `ownerAccountId() == null` pour les installations anonymes.
- `LocalAccountAccess.assertOwned()` refuse explicitement l'absence de propriétaire ; `protect()` exige `owned: true` par défaut.
- `DriftLibraryRepository.watchCourses()` exécute une jointure entre catalogue public et suivis privés, puis exige `assertOwned()` lorsqu'un suivi existe. Cela empêche une divulgation évidente mais peut bloquer le catalogue public en cas de données orphelines ; une séparation des requêtes publiques et privées serait préférable, sous réserve de tests Flutter.
- Les annulations de tâches de fond et les opérations en cours lors d'une déconnexion ne sont pas certifiées.

## Décision
**Point C non certifié.** Il reste impérativement à exécuter `flutter pub get`, `flutter analyze`, `flutter test` et la régression backend complète dans un environnement doté des SDK et du temps d'exécution requis. Les essais sur appareils réels restent en Phase 23.

Aucune correction Dart hasardeuse n'a été introduite sans possibilité de compilation. Ce checkpoint fournit des preuves supplémentaires et un état honnête des blocages.

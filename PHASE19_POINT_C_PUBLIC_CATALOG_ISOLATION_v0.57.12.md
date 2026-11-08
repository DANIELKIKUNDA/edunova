# EduNova — Phase 19 / Point C — v0.57.12

## Correction de l'isolation catalogue public / suivis privés

Fichier modifié : `apps/mobile/lib/src/features/library/infrastructure/drift_library_repository.dart`.

- Consultation anonyme : requête exclusivement sur `localLibraryCourses`, sans lecture ni jointure des suivis privés.
- Consultation authentifiée : jointure des suivis réservée au propriétaire authentifié.
- Les deux flux vérifient la génération de session avant chaque émission.
- Le flux anonyme refuse de poursuivre si un propriétaire apparaît entre-temps ; un nouvel abonnement est nécessaire.

## Preuves et limites

- Tests backend ciblés : 31/31 PASS (`test_identity_security`, `test_phase18_license_status_authorization`, `test_security_headers_lot28`, `test_sync*`).
- Flutter/Dart SDK absents : aucune compilation ni test Dart exécutés dans cet environnement.
- Régression backend intégrale : non validée.
- GitHub Actions : workflow présent, mais pas encore exécuté sur un dépôt distant.

## Décision

Phase 19 point C : EN COURS. Ne pas déclarer la certification Flutter acquise.

# EduNova v0.56.4 — Phase 19, Point A — Audit des repositories locaux

## Périmètre traité

- `DriftAcademicProfileRepository`: contrôle d’accès avant lecture, sauvegarde et chaque émission du flux du profil.
- `DriftAnalyticsRepository`: contrôle d’accès avant calcul des statistiques, sauvegarde du feedback et chaque émission du flux de feedback.
- `DriftEngagementRepository`: contrôle d’accès avant les opérations asynchrones de préférences, statistiques d’activité, notifications et streak; vérification à chaque émission des quatre flux.
- `DriftLibraryRepository`: contrôle avant modification des abonnements/suivis de cours. Le catalogue public reste consultable sans authentification; les cours suivis sont présents dans `watchCourses()` et doivent encore être isolés avant clôture.

## Vérifications exécutées

- Backend synchronisation : `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*` : **17 passed** (13.04 s).
- Dart/Flutter : **non exécutés** (SDK indisponible). Les modifications Dart ne sont donc pas certifiées par compilation.

## Risques ouverts et décision

- `LocalAccountAccess.assertReadable()` autorise actuellement l’installation sans propriétaire. Le contrôle des anciennes données orphelines existe au niveau de l’identité et du bootstrap, mais n’est pas imposé par tous les repositories. Cette politique doit être durcie pour les projections personnelles sans casser l’expérience offline-first neuve.
- `DriftLibraryRepository.watchCourses()` expose l’état personnel `followed` au sein du catalogue public : isoler le suivi privé ou filtrer pour les sessions non autorisées.
- Vérifier les autres repositories (audio, livraison, commerce, sync) et les opérations en cours lors de la déconnexion.
- Les contrôles effectués au début des méthodes ne constituent pas une garantie transactionnelle contre une déconnexion en milieu d’opération.

**Point A : non clôturé.** Ce checkpoint renforce quatre repositories, sans prétendre couvrir l’ensemble des accès locaux ni certifier Flutter.

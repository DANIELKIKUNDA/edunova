# EduNova — Phase 19, point A — Audit des accès repositories (v0.56.2)

## Correctif réalisé

- Ajout `apps/mobile/lib/src/core/security/local_account_access.dart` : contrôle de session à chaque lecture et émission de flux pour une installation dont le propriétaire est connu. En cas de déconnexion, d'incohérence de propriétaire ou d'erreur du stockage sécurisé, l'accès est refusé.
- Application de cette protection à `DriftPersonalDocumentRepository` (save, getById, watchAll, delete). La vérification se fait au niveau repository et non uniquement au routeur.
- La politique offline-first anonyme sur une installation neuve est conservée ; son inspection préalable reste la responsabilité du bootstrap.

## Audit et limites

- Les repositories `DriftDocumentWorkspaceRepository`, `DriftPedagogyRepository`, `DriftStudyPlanRepository`, `DriftAssistantRepository` et d'autres utilisent encore directement `AppDatabase` sans contrôle homogène de session au niveau repository. **Le point A n'est donc pas clôturé.**
- La protection des flux vérifie l'identité avant chaque émission, mais n'annule pas automatiquement les abonnements déjà ouverts lors de la déconnexion ; leur invalidation doit être auditée.
- La politique mono-propriétaire par installation ne constitue pas une séparation multi-comptes au niveau SQLite.
- SDK Flutter/Dart absent de cet environnement : compilation et tests Flutter **non exécutés**. Les changements Dart restent à valider.

## Vérifications exécutées

- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*` : **17 passed** (10.97 s). Ces tests backend ne couvrent pas le correctif Dart.
- ZIP généré et intégrité testée séparément.

## Prochaine intervention ciblée

Étendre les contrôles aux autres repositories privés et traiter l'invalidation des streams au logout, puis effectuer la validation Flutter dans un environnement équipé du SDK.

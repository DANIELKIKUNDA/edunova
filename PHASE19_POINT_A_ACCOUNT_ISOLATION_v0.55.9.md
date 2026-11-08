# EduNova v0.55.9 — Phase 19 / Point A

## Correction
- Détection des fichiers téléchargés dans `offline_library` sur les installations natives sans propriétaire connu, y compris si les tables SQLite sont vides.
- Rejet de la revendication d'une telle installation (`unowned_legacy_offline_files`) ; aucun effacement ni transfert implicite.
- Import conditionnel : sur le Web, les chunks restent dans SQLite et le détecteur natif n'est pas appelé.

## Contrôles
- Backend synchronisation : 17/17 PASS (`PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*`).
- Flutter SDK absent : compilation et tests Dart non exécutés. Les changements Flutter nécessitent validation sur CI avec Flutter SDK.

## Statut
Point A non certifié : restent l'audit exhaustif des accès directs aux données locales et les tests Flutter (dont héritage des fichiers natifs). Le choix architectural actuel est un seul propriétaire par installation, pas un stockage multi-compte.

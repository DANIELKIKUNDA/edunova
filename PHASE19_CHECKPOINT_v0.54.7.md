# EduNova v0.54.7 — Phase 19, protection des changements de compte

## Implémenté
- Vérification de l'identité de session après les appels réseau et avant les écritures de synchronisation : enregistrement appareil, résultats d'envoi, snapshot, pages de téléchargement, accusés de réception.
- Suppression de l'écriture de l'erreur de l'ancien compte après changement de session.
- Détection des entités dupliquées dans un snapshot canonique avant son application.
- Test Flutter ajouté : changement de compte pendant une requête push bloquée, aucun résultat ancien appliqué.

## Vérification réelle
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : 17 réussis.
- Flutter SDK absent : tests Dart/Flutter et compilation non exécutés.
- Ce contrôle ne constitue pas une certification de la Phase 19. Des contrôles complets offline/UX, tests Flutter et régression générale restent nécessaires.

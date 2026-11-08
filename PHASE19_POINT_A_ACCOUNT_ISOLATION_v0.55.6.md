# EduNova — Phase 19 / Point A — checkpoint v0.55.6

## Portée
Modèle conservateur **un propriétaire par installation** : les tables métier SQLite restent globales. Cette version n'implémente **pas** de multi-compte local.

## Corrections supplémentaires
- `SecureSessionStore`: sérialisation des lectures, sauvegardes et déconnexions dans un même isolate Dart, y compris entre instances, pour empêcher les courses entre deux connexions et les lectures de jetons partiellement enregistrés.
- Les écritures de jetons sont séquentielles après la fixation du propriétaire.
- Ajout de `secure_session_account_ownership_test.dart` : propriétaire après déconnexion, sauvegardes concurrentes, reprise d'une session héritée.

## Validation réellement exécutée
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync*` : **17/17 PASS**.
- Tests Flutter ajoutés mais **non exécutés** : SDK Flutter absent de cet environnement.

## Risques résiduels / décision de clôture
1. Une installation ancienne avec données SQLite mais sans marqueur propriétaire **et sans session conservée** ne peut pas attribuer sûrement ces données à un compte. Ce cas nécessite un parcours explicite de récupération ou de quarantaine des données, sans attribution automatique.
2. La sérialisation Dart est **par isolate**, non inter-processus et non atomique entre le stockage sécurisé et SQLite.
3. Les fichiers personnels stockés hors SQLite nécessitent un audit d'accès distinct.
4. Tests Flutter et scénarios d'intégration sur la connexion/déconnexion obligatoires avant certification.

**État : point A en consolidation, non certifié final.** Ne pas passer au point B avant la levée ou l'acceptation explicite de ces risques.

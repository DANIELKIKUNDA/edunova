# EduNova v0.52.7 — Phase 17, lot de clôture fonctionnelle

## Fonctionnalités implémentées et raccordées
- Gouvernance des membres centraux et protection du rôle propriétaire (lots précédents).
- Contrôle institutionnel, annuaire paginé, indicateurs et audit central (lots précédents).
- **Affectation d'administrateurs aux universités** : invitation `admin`/`academic_admin`/`faculty_admin` via `campus_memberships` existante, état `invited`, révocation `revoked`, contrôle de version, interdiction de toucher aux rôles propriétaire/recteur ou aux comptes étudiants; contrôle d'institution active et de compte actif.
- **Support central** : tickets institutionnels séparés des données étudiants, cycle `open → in_progress → resolved → closed`, contrôle de version, opérateur assigné actif et habilité, filtrage et pagination, audit.
- **Flutter administration** : consultation des administrateurs d'une université, invitation/révocation avec confirmation, tickets et avancement des états, accès conditionné aux permissions renvoyées par le serveur.
- Migration `0097_platform_support_tickets_v0_52_7.sql`; nouveaux événements centraux explicitement autorisés dans le journal.
- Workflow GitHub Actions Phase 17 mis à jour pour exécuter les nouveaux tests.

## Contrôles effectivement exécutés
- 21 tests ciblés Phase 17 et gouvernance : PASS.
- 1086 tests backend recensés par collecte pytest.
- Régression complète backend tentée : au moins un échec observé vers 35 % de progression; pas de PASS global revendiqué. Voir `phase17_0527_full.log` dans les pièces jointes séparées si disponible.
- Flutter SDK absent de cet environnement : `flutter analyze`, `flutter test` et build Flutter non exécutés.
- Aucun accès GitHub au dépôt du projet : workflow préparé, non exécuté sur GitHub.

## Décision de passage
Le périmètre fonctionnel défini de la Phase 17 (gouvernance centrale, institutions, affectations, support, audit, indicateurs, Flutter) est **implémenté dans le code**. La Phase 17 n'est **pas certifiée** : une régression globale a montré un échec, et les validations Flutter/CI/appareils restent à faire sur la machine de l'utilisateur. Ne pas confondre clôture de développement fonctionnel et validation qualité.

## Risques et suite
- Examiner l'échec de régression complète, puis relancer la suite jusqu'à 100 % PASS.
- Vérifier les migrations sur PostgreSQL de production/staging avant déploiement.
- Exécuter le workflow `.github/workflows/phase17-governance.yml` et les tests Flutter réels.
- Confirmer que le parcours d'acceptation d'invitation existant fonctionne pour les rôles institutionnels.
- Ne pas exposer le contenu des tickets à des comptes sans `platform.support.read`.

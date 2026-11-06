# EduNova v0.55.3 — garde de séparation des comptes (mode conservateur)

## Constat architectural
Les tables de projection SQLite `localAcademicProfiles`, `localAcademicEvents`, `localTimetableEntries`, `localReadingProgress`, `localLibraryCourseFollows`, `localObjectiveMastery` et `localPlanningPreferences` ne portent pas toutes un identifiant de compte. Le registre des versions est compartimenté, mais les données projetées ne le sont pas. Une synchronisation successive de comptes distincts dans une même base n'est donc **pas sûre**.

## Correction livrée
- `ensureState` refuse explicitement un deuxième compte (`cloud_sync_shared_database_account_switch_unsupported`) tant que les projections restent globales.
- Initialisation du premier compte et appropriation des mutations anonymes sous une transaction unique; relecture des états dans la transaction.
- Vérification appliquée aussi aux opérations d'envoi, de projection distante, de reset canonique et de résolution des conflits.
- Pas de suppression automatique des données du compte initial et pas de migration destructive.

## Limite assumée
Cette livraison est une **protection de confidentialité conservatrice**, et **non** la prise en charge complète du changement de compte. Pour permettre plusieurs comptes sur un appareil, il faut migrer les projections et tous leurs accès avec `accountId` (ou créer une base distincte par compte), puis tester la migration et les vues Flutter. Les écrans métier locaux hors synchronisation utilisent encore des tables partagées; ils ne sont pas isolés par ce garde-fou. Ne pas présenter cette version comme une certification multi-compte.

## Vérifications
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_sync_lot7.py` : 17 PASS.
- Tests Flutter et compilation : non exécutés (SDK absent).
- Validation de la régression mobile multi-compte : non exécutée.
- Phase 19 : non certifiée, le blocage de migration multi-compte et la validation Flutter subsistent.

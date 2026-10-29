# EduNova v0.52.8 — Correction de régression Phase 17

## Diagnostic reproductible
Le test `test_production_migrations_cover_all_sqlalchemy_tables_exactly_once` échouait car sa liste fermée de migrations s'arrêtait à `0095`, tandis que les migrations de Phase 17 `0096_platform_institution_controls_v0_52_3.sql` et `0097_platform_support_tickets_v0_52_7.sql` sont présentes. Le problème était dans le contrat de test, et non une migration absente.

## Correction
Ajout des deux migrations à la liste attendue dans `services/api/tests/test_migration_contract.py`. Le contrôle continue de vérifier l'égalité exacte avec les fichiers et la couverture des tables SQLAlchemy, sans affaiblir ses assertions.

## Résultats locaux
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_migration_contract.py services/api/tests/test_library_lot7.py` : **10/10 PASS**.
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_platform_governance* services/api/tests/test_migration_contract.py` : **9/9 PASS**.
- Régression globale : relance précédente interrompue par délai d'exécution; **aucun résultat global PASS revendiqué**.
- Flutter SDK, CI GitHub et tests appareil : non exécutés ici.

## Décision
Défaut de contrat de migration corrigé. Phase 17 : correctif local validé, certification globale encore à effectuer.

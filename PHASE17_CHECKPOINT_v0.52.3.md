# EduNova v0.52.3 — Phase 17, lot 4 : gouvernance institutionnelle effective

## Réalisé
- Nouvelle migration SQL `0096_platform_institution_controls_v0_52_3.sql` : historique courant de la décision centrale, motif, auteur, version optimiste.
- Nouveau dépôt `InstitutionControlRepository` : transactions atomiques modifiant à la fois le registre de décision **et l'état canonique** de l'établissement (`institutions.state`). Le contrôle de concurrence empêche les écritures périmées.
- API plateforme `GET /v1/platform/institutions/controls` (permission `platform.institutions.read`) et `PUT /v1/platform/institutions/{institution_id}/control` (permission `platform.institutions.manage`).
- Sécurité : institution existante obligatoire ; établissement archivé non réactivable ; statut limité à actif/suspendu ; motif obligatoire ; contrôle des rôles ; audit de décision ; aucune donnée privée exposée par ces endpoints.
- Permission de gestion explicitement accordée au propriétaire Volcano Tech, et maintenue pour l'administrateur plateforme.
- Flutter admin : affichage des décisions institutionnelles, contrôle de statut avec confirmation et motif, conflit de version géré, accès par permission.
- CI Phase 17 : nouveaux tests intégrés au job backend.
- Versions API et Flutter administration 0.52.3.

## Preuves locales
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_campus_api_lot22.py services/api/tests/test_phase17_institution_control_v0523.py services/api/tests/test_platform_governance_recovery.py services/api/tests/test_platform_governance_owner_isolation.py services/api/tests/test_phase17_flutter_governance_contract.py` : **15 passed**.
- Compilation syntaxique Python des modules de gouvernance : réussite.
- Tests Flutter, compilation Flutter et GitHub Actions distants non exécutés ici (SDK et dépôt GitHub non disponibles).

## Limitations et travaux restants
- Le registre liste les établissements ayant reçu une décision centrale ; il ne constitue pas encore un annuaire complet des universités. Il faut ajouter une vue centrale paginée des établissements existants.
- L'audit applicatif est écrit après la transaction institutionnelle ; en cas de panne de l'audit, une décision peut être validée sans ligne d'audit. Pour une garantie atomique complète, introduire une outbox transactionnelle.
- L'interface Flutter doit être compilée/testée sur SDK réel ; aucun PASS Flutter revendiqué.
- La Phase 17 reste ouverte : affectation d'administrateurs institutionnels, support central, analytics agrégés et certification.

# EduNova v0.51.2 — Phase 16 / Gouvernance des prêts physiques

## Origine et non-régression
- Checkpoint de départ : EduNova_v0.51.1_RC_PHASE16_PHYSICAL_LIBRARY_CIRCULATION.zip.
- SHA-256 du ZIP de départ : `223f084e4f959a948fe6fdfbdad293a93dc5047f9d3f1c73abe1ab4d24d9dbed`.
- Aucun module de catalogue pédagogique numérique n'a été reconstruit. La réservation des salles et le reste des Phases 0–15 sont conservés.
- Phase 16 **EN COURS**. Phases 14–15 : backend local validé précédemment, Flutter non certifié.

## Développement implémenté (backend + frontend)
- Politique locale provisoire du service de bibliothèque physique : **3 prêts ouverts maximum par membre**, **21 jours** par emprunt, **2 prolongations au maximum de 14 jours** chacune.
- Emprunt et prolongation refusés lorsqu'un prêt ouvert de l'emprunteur est échu (comparaison `due_at <= now`). Après restitution du retard, emprunter à nouveau redevient possible si le quota le permet.
- Vérification du quota **dans la même transaction** que l'insertion du prêt. PostgreSQL : verrou consultatif transactionnel par institution/emprunteur pour sérialiser les opérations portant sur différentes copies. L'unicité partielle existante par exemplaire reste le dernier rempart contre les doublons.
- Prolongation via `POST /v1/campus-services/institutions/{institution_id}/library/loans/{loan_id}/renew`, `expected_version` obligatoire, version optimiste ; emprunteur déterminé uniquement par le bearer token. Seul l'emprunteur actif peut prolonger, jamais un auditeur ou un autre membre ; l'administrateur peut toujours enregistrer une restitution.
- Traçabilité sur le prêt : compteur de prolongations, instant de dernière prolongation, version de ligne et journal d'audit de l'action ; aucune modification des anciennes notes ou finances.
- API de consultation enrichie par les indicateurs de retard et la capacité effective à demander une prolongation (`can_renew`), calculée à partir **de tous les prêts ouverts** de l'emprunteur, et non des résultats paginés.
- Application Flutter : gateway authentifié, action de prolongation, affichage des retards, compteur de prolongations, menu contextuel utilisable sur petit écran, rappel visible des règles ; protections existantes lors des changements de tenant et de session préservées.
- Migration **0088_campus_library_circulation_policy_v0_51_2.sql** : ajout de `renewal_count` avec valeur par défaut `0` pour les prêts historiques, `last_renewed_at`, contrainte CHECK et index partiel de suivi des retards.

## Tests et preuves effectives
- Régression *avant intervention* : **921/921 PASS** sur le ZIP original (voir journal dans le dossier des preuves).
- Nouveaux tests adversariaux/positifs : **18**, dont quotas, retards, isolation multi-universités, interdiction de prolonger le prêt d'autrui, versions périmées, restitutions et API FastAPI.
- Tests ciblés : **28/28 PASS**, `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_phase16_library_governance_v0_51_2.py services/api/tests/test_phase16_physical_library_v0_51_1.py services/api/tests/test_migration_contract.py`.
- Régression globale finale : **939/939 PASS, code retour 0**, `PYTHONPATH=services/api python -m pytest -q services/api/tests`; durée rapportée par pytest : **89,54 secondes**.
- `python -m compileall -q services/api/app services/api/tests/test_phase16_library_governance_v0_51_2.py scripts/audit_phase16_library_governance_v0_51_2.py` : PASS.
- Audit structurel de câblage : **20/20 PASS** ; **NE REMPLACE PAS** une compilation Flutter.
- Un passage global intermédiaire (non certifiant) s'est soldé par des erreurs SQLite « attempt to write a readonly database » pendant que plusieurs suites de tests étaient actives. La suite complète a été relancée **isolément après arrêt des autres exécutions** et s'est terminée avec 939 PASS. Le journal final seul fonde le statut PASS.

## Périmètre non exécuté et limites explicites
- **SDK Flutter/Dart absent** : `flutter analyze`, `flutter test` (un test du gateway prolongation a été ajouté) et `flutter build` **NON exécutés**. Pas de certification frontend.
- Migration 0088 **non appliquée sur PostgreSQL réel** ; test PostgreSQL transactionnel multi-processus du verrou consultatif et de l'index unique partiel **NON exécuté**. Tests backend fonctionnels basés notamment sur SQLite et sur métadonnées ORM.
- Redis / stockage objet / providers / terminaux et appareils réels **NON certifiés**.
- La politique de prêts (3 / 21 / 2×14) est **fixe** en v0.51.2 et n'est pas un règlement bibliothécaire configurable par université. Pas de pénalités financières ni de notification automatique de retard livrées.
- Catalogue, prêts et disponibilités ont encore des lectures bornées à 250 lignes ; recherche et pagination à renforcer. Gestion perte/dégradation, délivrance au comptoir, réservation académique, maintenance d'équipements, événements et alumni restent ouverts dans la Phase 16.
- Pas de garantie absolue de concurrence inter-processus avant les tests PostgreSQL réels. Aucun test sur appareils physiques.

**Décision :** checkpoint **v0.51.2** développé et backend vérifié localement ; frontend intégré non compilé ; **Phase 16 toujours EN COURS**.

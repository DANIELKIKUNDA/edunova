# EduNova v0.50.5 — CHECKPOINT CANONIQUE, Phase 15

- Date : 15 octobre 2026.
- Base obligatoire : `EduNova_v0.50.4_RC_PHASE15_PEER_COHORT_PRIVACY.zip`; SHA-256 d'entrée `6ac66e9952e497b12f0ebdaaba3524f9286313f869bfef159ab34791798390e2`.
- Version candidate produite : **EduNova v0.50.5 — Legacy Analytics Privacy Closure**.
- Phase 15 **EN COURS**, Phase 16 **NON COMMENCÉE** ; roadmap 0–26 inchangée.
- Fichiers de code modifiés :
  * `services/api/app/modules/institutional_analytics/application/service.py`
  * `services/api/app/modules/institutional_analytics/infrastructure/sqlalchemy_repo.py`
- Tests : `services/api/tests/test_phase15_legacy_surface_closure.py` (nouveau, 21 scénarios) et adaptation explicitement justifiée des assertions historiques `services/api/tests/test_institutional_analytics_lot27.py`.
- Les anciennes routes dashboards/signaux/CSV/rapports exécutifs ne peuvent plus contourner les contrôles de confidentialité Phase 15. Les enseignants et responsables de faculté sont maintenant limités à leur périmètre précis.
- Archives anciennes v1/v2 : métadonnées seulement en lecture, pas de payload ni d'empreinte. Nouvelles archives gouvernées : version 3 ; comparaison uniquement entre archives actuellement communicables.
- Agrégateur pédagogique historique : fail-closed, sans publication de tentatives non certifiées ; ce contrat reste à reconstituer avant réactivation.
- Dernière migration : **0084**, aucune nouvelle migration.
- **Baseline : 837/837 PASS. Final : 858/858 PASS, code retour 0. Audit : 17/17 PASS. Compilation Python : PASS.**
- Non certifié : Flutter, PostgreSQL/Redis réels, stockage objet réel, appareils, performance et confidentialité différentielle/risques temporels.

Détails : `RAPPORT_TECHNIQUE_PHASE15_v0.50.5.md` et `TEST_EVIDENCE_PHASE15_v0.50.5.txt`.

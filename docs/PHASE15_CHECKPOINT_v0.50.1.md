# Checkpoint EduNova v0.50.1 — Phase 15 (en cours)

Source canonique exacte : `EduNova_v0.50.0_RC_PHASE15_INSTITUTIONAL_INTELLIGENCE_FOUNDATION.zip` ; SHA-256 `eb441d643f525eb7ade8ebc69fdc61b0da062a1f7ea8d5a35f886a46d109b688`.

Nouvelle route : `GET /v1/institutional-analytics/institutions/{iid}/intelligence/period-comparison`.
Contrôles nouveaux : comparabilité de périodes, populations disjointes, suppression si <5 par période, sécurité des taux de soumissions, métadonnées de provenance. Tests réels dans `services/api/tests/test_phase15_period_comparison.py`.

Migration nouvelle : aucune. Dernière migration conservée `0084`. La Phase 14 backend local reste close, la Phase 15 reste en cours. L'information de validation test et l'empreinte du ZIP sont consignées dans `docs/PHASE15_RAPPORT_TECHNIQUE_v0.50.1.md` et `docs/certification/PHASE15_v0.50.1_EXECUTION.txt`.

Travaux non clos pour la Phase 15 : provenance détaillée des sources / complétude des cohortes, politique anti-différenciation inter-requêtes, analyse institutionnelle longitudinale avec preuves conformes, UX des décideurs, certification future.

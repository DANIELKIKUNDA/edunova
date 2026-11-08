# EduNova v0.49.7 — Phase 14 : intégrité des cohortes et preuves académiques

**Checkpoint source :** `EduNova_v0.49.6_RC_PHASE14_MAXIMUM_DEPTH.zip`, SHA-256
`a633692dcf8a68381f76bde9d444e5038f6979e1adf782e50583e0d259ccb3b9`.
La Phase 14 continue sans reconstruire les modules académiques / Campus existants et sans changer la roadmap.

## Défauts corrigés (code exécuté)

1. **Rapport cours/enseignant et périmètre de cohorte :** `offering_report` transmet maintenant au dépôt les comptes des **inscriptions actives de la cohorte de l'offre et de la même institution**. Le dénominateur de couverture est ce groupe, y compris les inscrits non encore notés ; aucun résultat d'un ancien inscrit / autre institution n'entre dans les agrégats.
2. **Preuves publiées :** filtre SQL explicite sur institution, offre **et cours du lien institutionnel** ; les doublons de résultats publiés pour un même compte (inscriptions de cours distinctes) sont écartés plutôt que comptés comme plusieurs étudiants. Pourcentages de notes non finis, négatifs ou supérieurs à 100 exclus. La publication officielle n'est jamais mutée par l'intelligence pédagogique.
3. **Présences :** seuls les enregistrements de sessions réellement clôturées et des inscrits actifs entrent dans le calcul. Une présence ne devient un *taux* que lorsque chaque étudiant actif possède un enregistrement pour chaque session clôturée ; sinon `attendance_rate=None` et `attendance_complete=False`. Les absences justifiées restent des absences (elles ne sont plus additionnées aux présences physiques). Une preuve de présence en examen de fraude (`needs_review` / `rejected`) bloque la publication du taux jusqu'à résolution.
4. **Cohorte vide :** aucun faux signal ni division par zéro ; `collect_more_evidence` avec confiance faible, sans note, sans score de présence ni hash de preuve.
5. **Petits groupes :** les traces explicatives du moteur déterministe n'incluent plus le taux d'échec, la note moyenne ou le taux de présence pour moins de trois évalués, y compris lorsqu'un appel direct fournit ces valeurs. La politique existante de suppression du rapport cours est maintenue.
6. **Robustesse des opérations existantes :** la signature d'accès aux preuves de cours conserve la lecture du curriculum pour `register_objective`, `map_question`, `bind_blueprint` ; aucun schéma, aucune migration ni opération d'écriture académique supplémentaire.

## Scénarios adversariaux ajoutés

- Identités retirées, institution étrangère, incohérence de cours, comptes évalués/non évalués ; zéro apprenant autorisé ; absence de lien cross-tenant.
- Doublons d'inscription publiés pour un même compte, notes infinies ou hors plage.
- Session ouverte ignorée, absence d'un enregistrement sur session clôturée, présence étrangère exclue, clôture complète avec présence/retard/absence, **absence justifiée non assimilée à une présence**, présence signalée en cours d'examen de fraude.
- Rapport vide sûr, suppression des marques sensibles sous le seuil de 3 évalués, filtrage bout-en-bout du service d'enseignement.

## Périmètre de certification

- Backend/Python/SQLite local et audit structurel : résultats exacts consignés dans `docs/certification/PHASE14_COURSE_COHORT_INTEGRITY_v0.49.7_TEST_EVIDENCE.txt`.
- Pas de migration nouvelle : dernière migration existante **0082**.
- Flutter/Dart, PostgreSQL réel, Redis, workers, stockage objet, appareils physiques et fournisseurs externes : **non certifiés sur cette version**. Une validation PostgreSQL reste requise à l'étape machine ; les tests SQLite ne prouvent pas une concurrence PostgreSQL réelle.
- Moteur explicable, déterministe, agrégé : aucune décision de jury, aucune notation, prédiction ou recommandation personnelle automatique.

**Statut :** Phase 14 encore en cours ; ce checkpoint renforce les preuves de cours, complémentairement aux preuves détaillées par objectif de v0.49.6.

## Résultats effectivement obtenus — vérification locale finale

- Baseline v0.49.6 reprise : **666/666 PASS** ; vérifiée avec la commande complète (`29.79s`).
- Candidat v0.49.7, commande complète `PYTHONPATH=services/api python -m pytest -q services/api/tests` : **672/672 PASS**, **31.04s**, code retour **0** ; régression réalisée en tâche détachée avec fichier de sortie et marqueur de fin, puis vérification effective de la terminaison.
- Test focalisé `test_phase14_pedagogical_intelligence.py` : **51/51 PASS**, code retour **0** (45 tests hérités + 6 nouveaux tests SQL/adversariaux).
- `python -m compileall -q services/api/app services/api/tests` : **PASS**, code retour **0**.
- `python scripts/audit_lot32_global.py` : **17/17 PASS**, code retour **0**.
- Aucune nouvelle migration ; dernier SQL `0082_pedagogical_objective_evidence_v0_49_2.sql`.
- Flutter compilation/test/analyze, certification PostgreSQL réel, Redis, stockage objet, machines et fournisseurs externes : **NON EXÉCUTÉS**.

## Fichiers effectivement modifiés

- `services/api/app/modules/pedagogical_intelligence/infrastructure.py`
- `services/api/app/modules/pedagogical_intelligence/application/service.py`
- `services/api/tests/test_phase14_pedagogical_intelligence.py`
- `services/api/app/version.py`
- `apps/mobile/pubspec.yaml` et `apps/admin/pubspec.yaml` (`0.49.7+105` ; version synchronisée, **aucune compilation Flutter déclarée**)
- `README.md`, le présent rapport et sa preuve d'exécution `docs/certification/PHASE14_COURSE_COHORT_INTEGRITY_v0.49.7_TEST_EVIDENCE.txt`.

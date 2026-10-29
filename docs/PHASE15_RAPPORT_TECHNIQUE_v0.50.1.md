# EduNova v0.50.1 — Rapport technique / Phase 15 : comparabilité et intégrité des agrégats

Date : 14 octobre 2026. Statut : **développement backend local vérifié** ; **Phase 15 ouverte**, certification machine et appareils non commencée.

## Chaîne de reprise

- Source canonique : `EduNova_v0.50.0_RC_PHASE15_INSTITUTIONAL_INTELLIGENCE_FOUNDATION.zip` ; SHA-256 vérifié : `eb441d643f525eb7ade8ebc69fdc61b0da062a1f7ea8d5a35f886a46d109b688`.
- Pré-développement : **785/785 tests backend PASS**, `pytest` code 0.
- Aucune migration introduite : dernière migration inchangée `0084_assessment_grading_snapshot_v0_49_12.sql`.
- Conservation des phases 0–14, pas d'implémentation d'un deuxième module analytique.

## Implémentation réelle

1. `services/api/app/modules/institutional_analytics/application/service.py`
   - Méthode `compare_period_briefs()` avec double validation RBAC/période/unité.
   - Correspondance de périodes successives, non chevauchantes, de même nature ; suppression globale des comparaisons si une population compte moins de 5 personnes uniques ou si les deux populations se recouvrent.
   - Comparaison uniquement de métriques déjà diffusables, définition versionnée et source contractuelle équivalentes ; différence en **points de pourcentage**. Les dénominateurs bruts et les comptes de recouvrement ne figurent pas dans les réponses.
   - Une publication d'un indicateur étudiant doit comporter une preuve de trois contributeurs distincts, sinon suppression « fail closed ». Ajout du contrat de provenance des cinq métriques.
2. `services/api/app/modules/institutional_analytics/infrastructure/sqlalchemy_repo.py`
   - `period_population_overlap()` : calcul SQL de populations uniques par période, tenant et unité ; aucun identifiant individuel restitué dans le contrat API.
   - Population éligible gouvernée limitée aux cohortes **actives, locales à l'université et conformes à la période**.
   - Opportunités de soumission basées sur inscriptions actives uniques par cohorte du bon tenant, non plus sur les inscriptions brutes qui pouvaient inclure les lignes étrangères.
   - Distinction des auteurs de soumissions pour la confidentialité des agrégats.
3. `services/api/app/modules/institutional_analytics/api/router.py`
   - Route authentifiée `GET /institutions/{iid}/intelligence/period-comparison` sous préfixe `/v1/institutional-analytics`.
4. `services/api/tests/test_phase15_period_comparison.py`
   - **11 nouveaux tests SQL réels**, incluant comparaison positive, petit groupe, chevauchement, type/ordre de période, RBAC, périmètre facultaire, comptes étrangers, données d'inscription étrangères, auteur unique, cohortes inactives, métadonnées de contributeurs absentes, et dépendance d'authentification.

## Vérifications exécutées

- `PYTHONPATH=services/api python -m pytest -q services/api/tests` (base v0.50.0) : **785/785 PASS** ; code 0.
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_phase15_period_comparison.py services/api/tests/test_phase15_institutional_intelligence.py services/api/tests/test_institutional_analytics_lot27.py` : **36/36 PASS** ; code 0.
- `PYTHONPATH=services/api python -m pytest -q services/api/tests` (v0.50.1, après les derniers changements) : **796/796 PASS** ; code 0 ; 57,34 s.
- `python scripts/audit_lot32_global.py` : **17/17 PASS** ; code 0.
- `python -m compileall -q services/api/app services/api/tests` : **PASS** ; code 0.
- ZIP : contrôle d'intégrité `ZipFile.testzip()` et SHA-256 inscrits dans le fichier d'empreinte accompagnant l'archive.

L'exécution initiale de la régression v0.50.1 en premier plan a dépassé le timeout de l'outil et a été interrompue, sans résultat concluant. Le test complet a ensuite été relancé avec redirection des sorties dans un fichier, attendu jusqu'à sa terminaison réelle, et **réexécuté après le dernier durcissement**. Les 796 PASS ci-dessus ne proviennent que du dernier run complet terminé.

## Limites et périmètre de certification

- Un seuil minimal et un filtrage de groupes disjoints **ne garantissent pas une anonymisation mathématique** ni une protection contre des requêtes multiples sur sous-périmètres ou à des instants différents. Aucun mécanisme de confidentialité différentielle ni budget de requêtes persisté n'est prétendu.
- Les indicateurs restent descriptifs et non causaux ; les dénominateurs issus de sources différentes ne sont pas substituables. Les mutations des données de production entre deux consultations peuvent affecter leur comparaison.
- Pas de compilation Flutter/Dart, test appareil réel, Redis réel, PostgreSQL réel, stockage objet externe, services de paiement ni validation juridique de signatures.
- Les contrôles ajoutés n'écrivent ni notes officielles, ni décisions du jury, ni fichiers Student Success.
- À poursuivre dans la Phase 15 : versionnage enrichi des provenances, comparaisons contrôlées interrequêtes, traçabilité de complétude des données, interface exécutive.

**Décision : v0.50.1 vérifiée localement ; Phase 15 maintenue EN COURS.**

# EduNova v0.49.6 — Phase 14 / Intelligence pédagogique
## Maximum-depth hardening — release candidate

**Continuité canonique.** Cette version dérive directement du ZIP
`EduNova_v0.49.5_RC_PHASE14_ADVERSARIAL_CLOSURE.zip`
(SHA-256 source : `e99aa6526b642ae46b67d910a5a5db9d552f3fdd112c79880380b3876ce7cd2e`).
Aucune reconstruction des domaines existants et aucun changement de phase.

### Portée réelle des modifications

1. **Dénominateur de couverture exact** : les tableaux par objectif comptent les comptes inscrits actifs autorisés dans `learner_count`, plutôt que de confondre inscrits et évalués. `assessed_count` reste le nombre d'apprenants avec preuves exploitables par objectif. Les cohortes sans copie corrigée ne produisent plus une fausse couverture à 100 %.
2. **Provenance anti-fraude** : une question du JSON de résultat n'est prise en compte que si elle figure dans `AttemptRow.question_ids` pour une tentative `graded` effectivement liée à l'offre. Les doublons d'identifiants de questions, valeurs non numériques, NaN, infinis, scores négatifs, scores supérieurs au maximum, et barèmes nuls sont écartés. Il n'y a aucune mutation des résultats officiels.
3. **Isolation des requêtes** : filtrage des apprenants admissibles directement dans les requêtes SQL d'extraction d'essais. Les blueprints restent filtrés par institution, offre et cours. Les cohortes vides ne récupèrent pas d'essais.
4. **Confidentialité des petits effectifs** : sous trois copies corrigées, les notes moyennes, nombres d'échecs, hashes d'évidence et volumes d'évidence détaillés sont masqués dans la projection par objectif. Les lignes de tendances n'apparaissent qu'à partir de trois évalués distincts ; les erreurs récurrentes exigent toujours au moins trois apprenants distincts. Au niveau rapport de cours, les notes/présences sont également masquées pour les petits groupes. Ce seuil est un *minimum cell-size safeguard*, pas une promesse d'anonymisation parfaite (les attaques par différenciation entre extractions restent à évaluer dans un environnement réel).
5. **Règles explicables conservatrices** : si moins de trois évalués, l'enseignant ne reçoit pas de conclusion de faiblesse collective ; seul `collect_more_evidence`, à confiance faible, est admis. Les valeurs non finies sont interdites. Les objectifs non évalués sont désormais effectivement classés `unassessed` (et non artificiellement `watch`).
6. **Liaisons immuables concurrentes** : les affectations question→objectif et blueprint→offre utilisent `INSERT ... ON CONFLICT DO NOTHING` suivi d'une comparaison du contenu enregistré. En cas de conflit, retour explicite au lieu de réaffectation silencieuse ; réitérations à l'identique idempotentes. Chemin PostgreSQL de production et SQLite de tests, pas de `merge` pouvant réécrire une liaison préexistante.

### Tests et certification effectués dans l'environnement ChatGPT

- À l'ouverture du ZIP v0.49.5 : **638/638 tests backend PASS** (exécutés dans cet environnement avant modifications).
- Version v0.49.6 : **666/666 tests backend PASS**, `PYTHONPATH=services/api python -m pytest -q services/api/tests`, durée 29,60 s, code retour 0.
- Tests Phase 14 : **45/45 PASS** (ancien total 17 ; 28 nouveaux), couvrant projections SQL SQLite réelles, filtrage cross-tenant, état de correction, fraude de question/résultat, doubles réponses, scores non finis, seuils de confidentialité, identités exclues, priorités sans preuves, immutabilité/idempotence.
- `python -m compileall -q services/api/app services/api/tests` : **PASS** (code 0).
- `python scripts/audit_lot32_global.py` : **17/17 PASS** (code 0).
- Aucune migration nouvelle : **schéma inchangé**, migrations préexistantes jusqu'à **0082**.

### Périmètre strict et validations non exécutées

- Régression : SQLite est ici le moteur local des tests d'intégration ; **concurrence PostgreSQL réelle non certifiée**, à faire sur infrastructure machine.
- PostgreSQL, Redis, workers, stockage objet et fournisseurs externes **non lancés** pour cette passe.
- Flutter et Dart **non installés** dans l'environnement ; versions de package synchronisées pour mobile/admin `0.49.6+104`, mais **aucun Flutter analyze/test/build ni essai sur appareil n'a été exécuté**.
- Moteur descriptif et déterministe uniquement ; aucune prédiction, diagnostic étudiant, notation automatique nouvelle, décision de jury, action Student Success automatique ni signature électronique qualifiée.

### Fichiers modifiés

- `services/api/app/modules/pedagogical_intelligence/infrastructure.py`
- `services/api/app/modules/pedagogical_intelligence/application/service.py`
- `services/api/tests/test_phase14_pedagogical_intelligence.py`
- `services/api/app/version.py`
- `apps/mobile/pubspec.yaml`, `apps/admin/pubspec.yaml`
- `README.md`, ce rapport, et la preuve d'exécution `docs/certification/PHASE14_MAXIMUM_DEPTH_v0.49.6_TEST_EVIDENCE.txt`.

**État au checkpoint** : Phase 14 approfondie, régression globale validée localement. Les validations d'infrastructure/appareils restent dans les phases de certification prévues de la roadmap figée.

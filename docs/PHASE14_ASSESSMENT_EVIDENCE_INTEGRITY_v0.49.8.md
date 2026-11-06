# EduNova v0.49.8 — Phase 14 : intégrité des preuves d’évaluation et des nouvelles tentatives

**Point de départ canonique** : `EduNova_v0.49.7_RC_PHASE14_COURSE_COHORT_INTEGRITY.zip` — SHA-256
`df489d8f7afcec95d525abb02727f883c32875d6850709b3f9e948580fa5cf58`.
**Objet** : continuer la Phase 14 sans refondre les modules Assessments, Academic Delivery ou Campus.

## Implémentation effective

1. **Catalogue canonique de questions** : les projections par objectif et les tendances n’acceptent une question que si `assessment_questions` contient encore cet identifiant dans le cours de l’offre, avec un barème positif concordant avec le résultat détaillé. Une correspondance `question→objectif` orpheline, un changement de cours ou une valeur de points divergente ne suffisent plus à produire de signal.
2. **Blueprint d’origine** : les tentatives ne contribuent qu’aux évaluations dont le blueprint existe réellement et dont le cours concorde avec celui lié à l’offre. Le simple enregistrement `blueprint→offre` ne constitue plus une preuve suffisante.
3. **Résultats JSON adversariaux** : pour un résultat comportant le verdict `correct`, ce booléen doit être valide et cohérent avec `earned/possible` selon la correction binaire actuellement utilisée par le moteur d’examen. Les doublons de questions dans `AttemptRow.question_ids` et les identifiants malformés sont rejetés sans exception serveur. Les anciens résultats ne contenant pas `correct` restent utilisables si les autres validations réussissent.
4. **Reprises d’évaluation** : une seule tentative notée est retenue par étudiant et blueprint : la dernière selon `submitted_at` (sinon `started_at`), puis l’identifiant comme départage déterministe. Ce choix est appliqué identiquement aux agrégats par objectif, aux tendances et aux erreurs récurrentes : une série de reprises ne peut plus surpondérer un étudiant. La dernière tentative invalide ne fait pas ressortir artificiellement une tentative antérieure : politique conservatrice de rejet de la preuve.
5. **Maintien des protections** : périmètre d’inscriptions actives, filtrage institution/offre/cours, cellules agrégées d’au moins trois étudiants évalués, absence de mutation des notes officielles, décisions pédagogiques déterministes non diagnostiques.

## Tests réels exécutés

- Source v0.49.7 : **672/672 PASS** (régression initiale en tâche détachée, code sortie 0).
- v0.49.8 : **681/681 PASS**, commande `PYTHONPATH=services/api python -m pytest -q services/api/tests`, code sortie **0**, **34.35 s** ; exécution en tâche détachée avec sortie et marqueur de terminaison.
- Tests ciblés Phase 14 : **60/60 PASS**, code sortie **0** (51 existants + 9 ajoutés).
- Compilation syntaxique : `python -m compileall -q services/api/app services/api/tests` **PASS**.
- Audit structurel : `python scripts/audit_lot32_global.py` **17/17 PASS**, code sortie **0**.
- Migration : **aucune migration ajoutée**, dernier SQL existant **0082** ; schéma inchangé.

### Scénarios adversariaux supplémentaires

- Reprise d’évaluation notée ne créant ni une copie supplémentaire ni une erreur récurrente artificielle.
- Question migrée vers un autre cours ou barème canonique divergent : aucune conclusion à partir de sa copie.
- Blueprint rattaché à un autre cours : aucune conclusion à partir des tentatives.
- Contradiction entre verdict de correction et score ; question répétée ; identifiant non hashable dans la liste de questions d'une tentative : rejet sans 500.
- Dernière reprise invalide : refus conservateur de ressusciter une ancienne copie.
- Projections descriptives entièrement en lecture seule : les `ResultRow.questions` restent inchangés après analyse.

## Limites et validations encore ouvertes

- Le contrôle des points lit le **catalogue courant**, qui n’est pas encore une photographie immuable/versionnée de l’énoncé au moment de la tentative. Un changement rétroactif de barème peut donc **supprimer** de la preuve historique ; le moteur refuse de fabriquer une équivalence inexistante. Ce durcissement ne certifie pas une chaîne de preuve immuable ni une équivalence psychométrique entre évaluations.
- La politique « dernière tentative notée » est un choix explicite **pour les tableaux pédagogiques seulement**. Elle ne modifie aucune règle de gradebook, jury ou résultat publié.
- Les tests d’intégration SQL utilisent **SQLite local**, pas PostgreSQL réel. Flutter/Dart compile/analyze/test, PostgreSQL, Redis, workers, stockage objet, appareils et fournisseurs externes : **NON EXÉCUTÉS**. Les certifications machine/appareil restent distinctes et prévues plus tard.
- Aucun apprentissage automatique, aucun diagnostic individuel, aucune notation automatique supplémentaire, aucune décision de jury.

## Fichiers modifiés par rapport à v0.49.7

- `services/api/app/modules/pedagogical_intelligence/infrastructure.py` : vérifications SQL source, cohérence des copies et déduplication des reprises.
- `services/api/tests/test_phase14_pedagogical_intelligence.py` : fixtures SQLite authentifiées et neuf tests additionnels.
- `services/api/app/version.py`, `apps/mobile/pubspec.yaml`, `apps/admin/pubspec.yaml` : versions 0.49.8 / Flutter 0.49.8+106 (version seulement, pas de compilation).
- `README.md` et le présent rapport, plus attestation d’exécution sous `docs/certification/`.

**Statut** : Phase 14 poursuivie ; backend statique/local certifié au périmètre exact ci-dessus. Ce rapport n'est pas une certification production.

# EduNova v0.51.0 — Phase 16 / Services physiques du Campus (foundation)

Le checkpoint v0.50.10 est conservé et étendu : première tranche effective de la Phase 16, réservations de salles/laboratoires/équipements et espaces de bibliothèque, contrôle RBAC, isolation multi-universités, prévention des chevauchements, écran Flutter et migration SQL 0086. **Phase 16 toujours en cours**, à ne pas confondre avec une clôture. Voir `CHECKPOINT_PHASE16_v0.51.0.md` pour le périmètre exact et les limites. Les Phases 14–15 conservent leur réserve de compilation Flutter.

---

# EduNova v0.50.9 — consolidation frontend Phases 14 et 15

Backend : 900/900 tests PASS. Interfaces Flutter ajoutées : gestion d'objectifs, associations de questions/évaluations, archives institutionnelles, aperçus CSV gouvernés et accès auditeur. Correctif de périmètre des administrateurs de faculté sur les preuves pédagogiques.

**Statut :** Code backend local vérifié ; nouveaux composants Flutter intégrés mais **pas certifiés** (SDK absent, tests Dart non exécutés). Selon la nouvelle règle de clôture, les Phases 14 et 15 ne sont donc **pas clôturées intégralement**. Phase 16 non commencée.

Voir `CHECKPOINT_PHASE14_15_FRONTEND_CONSOLIDATION_v0.50.9.md` et `RAPPORT_TECHNIQUE_PHASE14_15_FRONTEND_v0.50.9.md`.

---

# EduNova v0.50.8 — Intégration Flutter Phases 14 + 15 (checkpoint)

Nouvelle règle de clôture : **backend ET frontend fonctionnel vérifiés** avant toute clôture intégrale d’une phase ; certification sur appareils réels en Phase 23. Depuis v0.50.7, nouveaux écrans réels Campus enseignants et institutionnels, 891/891 tests backend PASS. **Flutter non compilé ici (SDK absent)** : Phases 14/15 fermées seulement pour le backend local, frontend en intégration ; Phase 16 non engagée.

Lire `CHECKPOINT_PHASE14_15_FRONTEND_BRIDGE_v0.50.8.md` et `RAPPORT_TECHNIQUE_PHASE14_15_FRONTEND_v0.50.8.md`.

---

# EduNova v0.50.7 — Phase 15 : clôture backend locale (candidate)

Checkpoint canonique backend local clôturé (889/889 tests PASS) : `EduNova_v0.50.7_RC_PHASE15_BACKEND_CLOSURE.zip`.
La Phase 15 est clôturée pour le périmètre backend vérifié localement après
889 tests réussis et un audit structurel 17/17 PASS. Les validations sur
PostgreSQL/Redis/stockage objet réels, la compilation Flutter et la certification
sur appareils restent réservées aux phases 22–24 selon la roadmap figée.

Nouveautés v0.50.7 : contrat temporel persistant des statistiques vivantes, preuve
HMAC de population ET contenu des archives v5, première archive autorisée
(non la dernière) tous filtres confondus, migration 0085 et nouveaux tests adversariaux.
La confidentialité transversale toutes requêtes/tous consommateurs et la performance
à grande échelle ne sont **pas** certifiées. Les taux publiés pour un périmètre
ne sont plus actualisés par simple nouveau GET si les données changent : les valeurs
sont masquées jusqu'à l'existence d'un mécanisme de republication gouverné et sûr.
Voir `RAPPORT_TECHNIQUE_PHASE15_v0.50.7.md`.

Current baseline: EduNova v0.47.2 RC — Phase 12 Official Documents Foundation.

Current baseline: EduNova v0.47.2 RC — Phase 11 Maximum Depth: Atomic Service Desk.

# EduNova v0.20.0 — LOT 19 — Intelligent Remediation Engine

LOT 19 turns evidence from learning, Error Bank and assessment into explainable misconception diagnosis and six-stage remediation: diagnose → explain → worked example → guided practice → transfer → independent reassessment. See `docs/LOT19_INTELLIGENT_REMEDIATION_v0.20.0.md` and ADR-024.


**Status ChatGPT:** LOT 18 backend/code/audit PASS; machine certification OPEN.

LOT 18 ajoute le moteur industriel d’évaluation: banques de questions versionnées et sourcées, blueprints d’examen, tentatives persistantes/reprenables, optimistic locking, correction explicable, provenance page/source, résultats par chapitre et UI Student Delight d’examen. Une question non approuvée n’entre pas dans un examen `approved_only`.

# EduNova v0.17.1 — LOT 16 FINAL Student Intelligence & Adaptive Learning

Premier checkpoint industriel du LOT 16: intelligence étudiante explicable, scoring déterministe, lacunes et priorités adaptatives, snapshots auditables et première surface mobile premium. Voir ADR-018.


## LOT 15 — Learning Experience Engine / Study Workspace

Le checkpoint v0.16.2 ajoute le bounded context étudiant: sessions persistantes, reprise précise, modes d’étude, progression sémantique (viewed/studied/practiced/assessed/mastered), Error Bank, répétition espacée, home learning et Study Workspace responsive premium. Voir `docs/LOT15_LEARNING_EXPERIENCE_v0.16.2.md` et ADR-017.

# EduNova v0.16.2 — LOT 15 Student Delight / UI-UX Signature Final
## v0.16.2 — Student Delight / UI-UX Signature Final

Passe finale d’attractivité étudiante: Study Workspace adaptatif et immersif, Focus mode, parcours de maîtrise, flashcards tactiles, quiz progressif, Exam Mode, micro-interactions sobres et doctrine Free/Premium non punitive. Voir `docs/LOT15_STUDENT_DELIGHT_v0.16.2.md`.


LOT 14 industrialise la publication contrôlée après validation Studio: releases versionnées, preflight, programmation, audience/rollout, droits Premium/offline, snapshots immuables SHA-256, retrait auditable et centre de publication. Aucun contenu non publié par la gouvernance éditoriale ne peut entrer dans une release.

# EduNova v0.14.2 — LOT 13 UI/UX Premium Final

Checkpoint UI/UX final du LOT 13, construit sur v0.14.1 sans modification du contrat métier. Le cockpit Content Factory devient un poste de revue responsive avec master-detail desktop, filtres/recherche/tri, états UX complets, revue artefact ↔ preuve source, quality gates et traçabilité. Voir `docs/LOT13_UIUX_PREMIUM_FINAL_v0.14.2.md`.

## Baseline moteur — v0.14.1 LOT 13 Content Factory industrielle

**Baseline préservée : v0.14.0 LOT 13, elle-même issue de v0.13.1 LOT 12 FINAL.**

LOT 13 transforme les résultats validés du pipeline d’ingestion en ressources pédagogiques traçables. La chaîne est : source LOT 12 → segmentation → artefacts pédagogiques → preuves page-level → quality gates → paquet de revue humaine → `READY_FOR_REVIEW`. **Aucune publication automatique.**

## Durcissements v0.14.1
- pipeline `content-factory-v1.1`, gouvernance `factory-governance-v2` ;
- contrôle bloquant de cardinalité des preuves ;
- vérification que chaque citation de preuve existe réellement dans le texte source normalisé ;
- vérification SHA-256 des citations ;
- garde bloquante des assertions numériques non présentes dans la preuve citée ;
- détection de quasi-doublons pédagogiques par similarité lexicale ;
- endpoint de paquet de revue `GET /v1/content-factory/runs/{id}/review-package` associant chaque artefact à sa preuve ;
- `publication_allowed=false` codé dans le paquet de revue ;
- annulation explicite d’un run en attente ;
- Studio : comparaison visuelle artefact ↔ extrait source/page dans le dossier de transformation ;
- versions API/Admin/Mobile 0.14.1, Flutter build +21.

## Capacités conservées
Plan structuré, résumés express/détaillés, concepts, flashcards, quiz, chunks RAG, SHA-256, provenance page-level, idempotence par source/pipeline/contrat, score qualité, rôles Studio, worker séparé, audit et intégration avec le LOT 12.

## Gouvernance
Le moteur peut préparer du contenu ; il ne peut pas le publier. Les contenus médicaux/high-stakes restent soumis à la revue humaine et aux règles de séparation des rôles du LOT 11.

## Certification
Voir `docs/certification/LOT13_FINAL_ACCEPTANCE_v0.14.1.md`. Les vérifications nécessitant Flutter, PostgreSQL concurrent réel, fournisseurs IA externes, navigateurs/appareils et charge massive restent `OPEN-machine`.


## v0.16.2 LOT 15 final hardening
Exam preparation plans, explainable study recommendations, Error Bank review lifecycle, defensive PostgreSQL learning-state constraints, and Study Workspace UX reinforcement. Backend 285/285 PASS; focused LOT 15 tests 9/9 PASS; Flutter/infrastructure certification remains OPEN-machine.

## v0.17.1 — LOT 16 FINAL maximal
- adaptive-v2: confiance fondée sur le volume de preuves, lacunes multi-signaux, préparation examen et matières à risque ;
- recommandations explicables avec urgence, résultat attendu et cause d'échéance ;
- historique de snapshots pour tendances auditables ;
- UI Student Intelligence premium responsive avec priorités, examen, lacunes et preuves ;
- garde-fou: les scores sont des indicateurs d'étude, jamais une prédiction de note ou une certitude de maîtrise.
- OPEN-machine: Flutter analyze/test/build, appareils réels, PostgreSQL concurrence, offline multi-device, charge/endurance.

## v0.18.0 — LOT 17 Adaptive Study Planner & Academic Orchestration
LOT 17 transforme les priorités explicables du LOT 16 en plans d'étude réalistes. Il respecte charge maximale, plages préférées, indisponibilités, buffers, examens, erreurs et répétitions espacées; expose l'overflow au lieu de surcharger; supporte done/skipped/replanification et une UI Jour/Semaine premium non punitive. Voir ADR-019. Certification machine reste OPEN-machine.

## v0.19.3 — LOT 17 FINAL maximal
Durcissement final du planner: index partiels d'exécution/replanification, préservation stricte des items terminés lors des régénérations, concurrence optimiste et certification backend shardée 293/293 PASS. UI/UX Jour/Semaine premium, explicable et non punitive. Machine gates restent OPEN-machine.

## v0.19.3 — LOT 18 Cognitive Intelligence Final
Assessment engineering is now Bloom-governed and quality-gated: explicit learning objectives, reasoning steps, distractor rationales, authentic context, cognitive blueprint distributions, fail-closed selection, CREATE constructed-response enforcement and by-Bloom result analytics. See `docs/LOT18_COGNITIVE_ASSESSMENT_INTELLIGENCE_v0.19.3.md` and ADR-022.

## v0.21.0 — LOT 20 Knowledge Graph & Academic Knowledge Intelligence
Governed academic concept graph with provenance, prerequisite/dependency reasoning, cycle prevention, high-stakes review gates and projections for adaptive learning, planning, assessment and remediation.

## Baseline v0.27.3 — LOT 26 FINAL Industrial Closure
Campus Operations is closed in the ChatGPT environment: secure attendance, institutional announcements, operational calendar, absence justification workflow, operational monitoring, Engagement notifications and auditable lifecycle controls. See `docs/LOT26_FINAL_INDUSTRIAL_CLOSURE_v0.27.3.md` and ADR-044.

## LOT 26 closure audit — v0.27.3
Contradictory audit completed: Campus server notifications now use remote PUSH intents; Firebase Admin FCM transport and Flutter Firebase Messaging registration are wired while local notifications remain offline-first. Real Firebase credentials/device delivery remain deployment certification, not repository secrets.

## RC v0.47.5
Phase 12 issuer provenance: immutable issuer identity + document template snapshot; migration 0075; 602 backend tests PASS.

## RC v0.47.6
Phase 12 maximum-depth hardening: governed institutional document templates (draft/published/retired), exactly one published template per institution/document kind, issuance blocked without a published template, immutable template version snapshot on every issued document, and atomic administrative correction that issues the corrected document while superseding/revoking the prior active document in the same transaction. Migration 0077.

- v0.49.5: Phase 14 adversarial hardening — enrollment-scoped evidence, conflict-safe mappings/bindings, aggregate-only provenance.
- v0.49.6: Phase 14 maximum-depth evidence hardening — cohort-denominator coverage, forged/duplicate/invalid result defenses, small-cell aggregate privacy, DB-atomic immutable assessment mappings and adversarial SQL regression. See `docs/PHASE14_MAXIMUM_DEPTH_v0.49.6.md`.

- v0.49.13: Phase 14 backend/static local closure: learning-objective mapping chronology (retrospective vs contemporaneous) and staff-only read-only comparison of candidate assessment references in published gradebooks. This **does not** authenticate gradebook/jury publication or certify real infrastructure; see `docs/PHASE14_CLOTURE_BACKEND_v0.49.13.md`.
- v0.49.12: Phase 14 immutable grading-time input snapshot v2, versioned checksum, PostgreSQL FOR SHARE staging, drift-safe teacher evidence across question edits/deletions, adversarial multi-tenant tests. Historical v0/v1 evidence retained unchanged. See `docs/PHASE14_GRADING_SNAPSHOT_v0.49.12.md`.
- v0.49.11: Phase 14 versioned, fully reconciled deterministic auto-scoring contract (migration 0083), atomic grade finalization, and explicit legacy/unverified provenance in teacher analytics. Historical grades remain unmodified. See `docs/PHASE14_SCORE_RECONCILIATION_v0.49.11.md`.
- v0.49.10: Phase 14 graded-attempt chronology and result-total provenance; latest-started retake wins and invalid timing/score aggregates fail closed without falling back to prior evidence. See `docs/PHASE14_ATTEMPT_RESULT_INTEGRITY_v0.49.10.md`.
- v0.49.9: Phase 14 institutional student identity deduplication, content-sensitive course evidence digests and fail-closed unsubmitted exam retakes. See `docs/PHASE14_IDENTITY_PROVENANCE_v0.49.9.md`.
- v0.49.8: Phase 14 canonical question/blueprint provenance and graded-retake integrity — fail-closed result validation and adversarial multi-tenant SQL regression. See `docs/PHASE14_ASSESSMENT_EVIDENCE_INTEGRITY_v0.49.8.md`.
- v0.49.7: Phase 14 canonical course-cohort integrity — active-enrollment denominators, published result provenance and duplication safeguards, attendance completeness and justified-absence semantics; adversarial SQLite integration regression. See `docs/PHASE14_COURSE_COHORT_INTEGRITY_v0.49.7.md`.

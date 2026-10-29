# EduNova v0.14.0 — LOT 13 Content Factory

## Mission
Transformer à cadence industrielle les documents validés par LOT 12 en ressources pédagogiques structurées, traçables et prêtes pour une revue humaine.

## Pipeline
`LOT12 SUCCEEDED → Factory Run → structure → résumés → concepts → flashcards → quiz → RAG chunks → provenance page → quality gates → READY_FOR_REVIEW`.

## Contrôles industriels
- idempotence par source/pipeline/contrat d'artefacts;
- empreinte SHA-256 des sources et de chaque artefact;
- evidence ledger page par page avec extrait et hash;
- quality gates bloquants/warnings/info;
- score qualité 0–100;
- audit des créations et fins de runs;
- états explicites queued/processing/ready_for_review/failed/cancelled;
- worker séparé et budget de tentatives;
- SQL PostgreSQL 0011 avec contraintes/index;
- API Studio dédiée `/v1/content-factory`;
- écran Studio responsive « Content Factory » avec KPI, runs, qualité, preuves et artefacts.

## Génération v1
Le moteur livré utilise une baseline déterministe source-grounded afin que le domaine, les preuves et les contrats soient certifiables sans dépendre d'un fournisseur IA. Les adaptateurs LLM pourront enrichir la qualité de rédaction dans un lot/hardening ultérieur sans modifier les invariants de provenance.

## Gouvernance
Aucune sortie LOT 13 n'est publiée. `READY_FOR_REVIEW` signifie uniquement que les contrôles automatiques sont passés et qu'un humain peut commencer la revue Studio.

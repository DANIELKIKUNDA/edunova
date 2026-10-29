# ADR-014 — LOT 13 Content Factory industrielle

## Décision
LOT 13 est un bounded context séparé de l'ingestion (LOT 12), du Studio éditorial (LOT 11) et de l'assistant (LOT 6). Il ne transforme que des artefacts d'ingestion réussis et immuables. La sortie terminale positive est `READY_FOR_REVIEW`; aucune publication automatique n'est autorisée.

## Invariants
1. Toute ressource générée possède un SHA-256 canonique et au moins une preuve source avec page(s), extrait et SHA-256 de l'extrait.
2. Le contexte académique et les droits du lot d'origine sont figés dans le run.
3. Un même document + version de pipeline + contrat d'artefacts est idempotent.
4. Les familles sont explicites: plan, résumés, concepts, flashcards, quiz, exercices et chunks RAG.
5. Les quality gates bloquants empêchent `READY_FOR_REVIEW`.
6. L'IA future est un adaptateur remplaçable; la provenance et la gouvernance appartiennent au domaine EduNova.
7. Production exécute la factory dans un worker séparé de FastAPI.

## Sécurité et high-stakes
Les sorties médicales/high-stakes restent des brouillons. Elles héritent de la séparation auteur/relecteur/publicateur du Studio. La génération n'est jamais une validation scientifique.

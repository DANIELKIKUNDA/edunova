# Baseline EduNova v0.7.1

LOT 6 — Assistant / RAG approfondi.

Cette baseline hérite de v0.7.0 et ajoute :
- cache versionné par langue, profondeur, historique borné et prompt version ;
- neutralisation réelle des prompt injections documentaires ;
- déduplication/diversification des chunks ;
- reranking déterministe sans coût IA ;
- multi-query retrieval borné pour comparaisons ;
- mémoire conversationnelle locale/éphémère (6 tours) ;
- profondeur pédagogique Essentiel / Standard / Approfondi ;
- contrôle post-réponse de grounding ;
- flags de contradictions numériques ;
- récupération par modèle supérieur si le premier modèle dérive ;
- remboursement du crédit utilisateur si la réponse finale est rejetée pour mauvais ancrage ;
- métriques grounding/source count/prompt version persistées localement ;
- Drift v10.

Backend certifié dans ChatGPT : **155/155 PASS**.
Flutter : certification machine ouverte.

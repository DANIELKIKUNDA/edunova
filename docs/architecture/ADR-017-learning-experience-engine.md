# ADR-017 — Learning Experience Engine
Status: Accepted for v0.16.0.

## Decision
Créer un bounded context `learning_experience` distinct de `pedagogy`, `analytics`, `planning` et `publication`. Les sessions sont des événements d'usage durables ; la maîtrise est un état pédagogique monotone et n'est jamais inférée du temps d'écran seul.

Une session ouverte est unique par compte au niveau base. Les checkpoints utilisent `row_version`. Les cartes de révision utilisent un calcul déterministe localisable côté client ultérieurement ; le serveur reste source de convergence multi-appareil.

## Offline-first
Le contrat API est conçu pour accepter des checkpoints idempotents/versionnés. La matérialisation Drift et la résolution de conflits multi-device restent une porte de certification/approfondissement LOT 15 avant fermeture finale.

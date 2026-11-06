# LOT 6 v0.7.1 — Critères d'acceptation approfondis

## Backend
- [x] Cache différencié par langue.
- [x] Cache différencié par profondeur pédagogique.
- [x] Cache différencié par version de prompt.
- [x] Cache différencié par historique conversationnel borné.
- [x] Prompt injection détectée et retirée avant contexte modèle.
- [x] Chunk dupliqué éliminé.
- [x] Reranking query-aware sans appel IA.
- [x] Compare => multi-query retrieval borné.
- [x] Contradictions numériques explicites => flag de revue.
- [x] Grounding post-réponse calculé.
- [x] Mauvais grounding => modèle suivant autorisé.
- [x] Mauvais grounding final => abstention + 0 crédit utilisateur.
- [x] Prompt version/source count/grounding exposés par API.
- [x] Mémoire conversationnelle limitée à 6 tours.
- [x] Conversation précédente séparée des sources académiques.
- [x] Batterie complète : 155/155 PASS.

## Mobile
- [x] Contrat API mémoire conversationnelle.
- [x] Profondeur Essentiel/Standard/Approfondi.
- [x] Drift v10 écrit.
- [x] Grounding/source count/prompt version persistables localement.
- [x] L'historique est envoyé depuis le stockage local uniquement.
- [ ] `build_runner` Flutter réel.
- [ ] `flutter analyze`.
- [ ] `flutter test`.
- [ ] build Android.
- [ ] build Web/PWA.
- [ ] build Windows.

## Production
- [ ] benchmark providers réel ;
- [ ] corpus médical réel pour calibration des seuils de grounding ;
- [ ] test de prompt-injection sur PDF réels ;
- [ ] mesure du taux d'abstention et des faux rejets ;
- [ ] test multi-worker Redis ;
- [ ] validation confidentialité avant documents personnels distants.

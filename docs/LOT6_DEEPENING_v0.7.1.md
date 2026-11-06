# LOT 6 — Approfondissement v0.7.1

## 1. RAG
- recherche multi-requêtes déterministe pour les comparaisons ;
- reranking local coût zéro ;
- diversité documentaire ;
- déduplication des passages redondants ;
- budget contexte conservateur ;
- prompt injection supprimée du contexte avant appel modèle.

## 2. Grounding après génération
EduNova calcule un indicateur de couverture de la réponse par la question et les sources. Ce n'est pas une mesure de vérité, mais un garde-fou contre la dérive hors cours.

- claims numériques absents des sources => flag ;
- contradictions numériques explicites entre sources => flag de revue ;
- faible couverture => confiance réduite ;
- couverture extrêmement faible => réponse rejetée et crédit utilisateur libéré ;
- fallback possible vers un modèle supérieur.

## 3. Conversation réelle, sans historique serveur
Les conversations restent dans SQLite/Drift. À chaque question, seuls les 6 derniers tours user/assistant sont envoyés éphémèrement. Ils servent au contexte conversationnel mais ne deviennent jamais des sources académiques.

## 4. Adaptation pédagogique
Trois profondeurs :
- Essentiel ;
- Standard ;
- Approfondi.

La profondeur fait partie de l'identité de cache.

## 5. Audit
Chaque réponse locale peut conserver :
- confiance ;
- grounding coverage ;
- nombre de sources ;
- provider/model ;
- crédits ;
- cache hit ;
- safety flags ;
- route reason ;
- prompt version.

## 6. Confidentialité
Pour un document personnel :
- consentement explicite ;
- extraits seulement ;
- pas de cache partagé ;
- pas de conversation serveur persistante ;
- historique local uniquement.

# ADR-0008 — LOT 6 approfondi : grounding, mémoire éphémère et cache versionné

## Décision
EduNova renforce l'assistant sans rendre le serveur propriétaire de l'historique étudiant.

1. Les derniers échanges restent stockés localement sur l'appareil et seuls les 6 derniers tours pertinents sont envoyés éphémèrement avec la question.
2. Le cache partagé inclut langue, profondeur pédagogique, version de prompt et historique borné afin d'éviter de réutiliser une réponse dans un contexte différent.
3. Les instructions suspectes présentes dans un PDF sont neutralisées avant construction du contexte, pas seulement signalées.
4. Les chunks sont dédupliqués, diversifiés et rerankés par requête sans appel IA supplémentaire.
5. Une réponse générée est contrôlée après génération : couverture lexicale par les sources, claims numériques nouveaux et contradictions numériques potentielles.
6. Une réponse très faiblement ancrée est rejetée. Le crédit utilisateur est libéré ; si un modèle suivant est disponible il peut tenter de récupérer la question. Le budget global conserve le coût réel du fournisseur déjà appelé.
7. Les métriques de grounding, source count et prompt version sont persistées localement pour audit.

## Raisons
- réduire les hallucinations ;
- rendre les suivis conversationnels réellement contextuels ;
- éviter les cache hits pédagogiquement faux ;
- résister aux prompt injections contenues dans des documents ;
- préserver la confidentialité et le modèle local-first ;
- rendre les incidents IA auditables sans journaliser les documents personnels sur le serveur.

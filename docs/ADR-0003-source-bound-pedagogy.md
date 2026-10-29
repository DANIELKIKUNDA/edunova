# ADR-0003 — Pédagogie liée aux sources

## Décision

Tout résumé, flashcard ou question généré à partir d’un cours conserve les références exactes `document/chunk/pages` utilisées. Le fournisseur IA est un adaptateur et ne peut pas publier directement du contenu collectif.

## Pourquoi

EduNova doit expliquer **le cours de l’étudiant**, permettre un retour au passage d’origine, limiter les hallucinations et rendre les corrections auditables.

## Conséquences

- les prompts sont versionnés ;
- le modèle/fournisseur est enregistré ;
- le contenu médical généré exige une revue humaine avant publication collective ;
- le contenu personnel peut rester privé sur l’appareil ;
- un changement de fournisseur IA ne change pas le domaine.

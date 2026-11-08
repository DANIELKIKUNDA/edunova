# ADR-011 — Gouvernance éditoriale EduNova

## Décision
EduNova Studio est un back-office privé de l'organisation EduNova. Il ne crée aucun rôle d'université.

Rôles internes minimaux :
- **Owner** : gouvernance de l'équipe et droits complets ;
- **Editor** : importe, structure et corrige ;
- **Reviewer** : contrôle le fond, la source et la qualité ;
- **Publisher** : décide de la mise en ligne après approbation.

## Workflow
`DRAFT → IN_REVIEW → APPROVED → PUBLISHED`

Branches : `CHANGES_REQUESTED`, `REJECTED`, `ARCHIVED`.

Une révision publiée n'est jamais modifiée. Pour mettre à jour un cours, l'équipe crée une nouvelle révision pendant que la version publiée reste active. La bibliothèque ne bascule vers la nouvelle révision qu'après nouvelle validation.

## Garde-fous
- droits de diffusion obligatoires avant revue/publication ;
- `INTERNAL_ONLY` ne peut jamais être publié ;
- contenu médical / high-stakes : règle des quatre yeux ;
- contenu IA : `prompt_version` obligatoire ;
- source/fingerprint obligatoire pour high-risk ;
- historique des révisions, décisions et publications immuable ;
- toutes les actions sensibles écrites dans l'audit global.

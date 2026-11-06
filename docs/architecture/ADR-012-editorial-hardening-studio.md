# ADR-012 — Editorial hardening & Studio professionnel

## Décision
EduNova adopte une gouvernance éditoriale optimistic-locking, revision-first et role-separated.

## Raisons
- éviter les écrasements concurrents ;
- garantir la traçabilité ;
- rendre défendables les contenus médicaux ;
- permettre la collaboration d'une petite équipe sans introduire des rôles universitaires ;
- conserver une ancienne version publiée pendant qu'une nouvelle version est préparée.

## Conséquences
- toutes les mutations critiques portent la version de ligne courante ;
- toute approbation est soutenue par une checklist ;
- publication high-stakes séparée de l'auteur et du relecteur ;
- archivage synchronisé avec le catalogue ;
- UX du Studio structurée autour de la fiche éditoriale et de files de travail.

# ADR-019 — Adaptive Study Planner & Academic Orchestration

## Décision
LOT 17 est un bounded context séparé. LOT 16 décide **quoi** prioriser; LOT 17 décide **quand** l'étudier, dans une capacité temporelle explicite. Le planificateur est déterministe, explicable et modifiable par l'étudiant.

## Invariants
- jamais dépasser silencieusement la limite quotidienne ; l'excédent est déclaré ;
- respecter les indisponibilités et l'horaire importé lorsqu'ils sont fournis ;
- priorité: continuité, erreurs, examen, répétition espacée, évaluation/pratique ;
- une session manquée déclenche une replanification, pas une pénalité de maîtrise ;
- optimistic locking sur préférences et items ;
- plan consultable offline côté client, synchronisation différée ;
- aucune prédiction de note.

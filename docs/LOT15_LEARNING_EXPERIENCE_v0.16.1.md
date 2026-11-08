# LOT 15 — Learning Experience Engine / Study Workspace — v0.16.1

## Mission
Transformer le catalogue publié en expérience d'étude quotidienne mesurable, offline-first et multi-appareil. Le LOT 15 distingue explicitement exposition, étude, pratique, évaluation et maîtrise.

## Chaîne
Catalogue LOT 14 → Study Workspace → session → checkpoint/reprise → pratique/évaluation → Error Bank + spaced repetition → progression → analytics/planning existants.

## Contrats livrés
- sessions `read`, `quick_review`, `flashcards`, `quiz`, `exercises`, `focus`, `exam` ;
- cycle active/paused/completed/abandoned, position de reprise et verrouillage optimiste ;
- une seule session ouverte par compte (contrainte PostgreSQL partielle) ;
- progression monotone `not_started → viewed → studied → practiced → assessed → mastered` ;
- ratio de complétion et précision séparés de la simple activité ;
- Error Bank et échéance de retravail ;
- répétition espacée déterministe inspirée SM-2, avec facteur d'aisance plancher ;
- home learning : reprise, temps étudié, erreurs ouvertes, cartes dues, unités maîtrisées ;
- Study Workspace Flutter adaptatif mobile/tablette/desktop avec focus mode et affordance offline.

## Frontière de responsabilité
Le LOT 15 consomme les contenus autorisés par LOT 14. Il ne publie pas, ne modifie pas le contenu éditorial, et ne remplace pas LOT 10 Analytics ni LOT 4 Planning : il produit les signaux d'apprentissage qui pourront les alimenter.


See also `LOT15_FINAL_HARDENING_v0.16.1.md`.

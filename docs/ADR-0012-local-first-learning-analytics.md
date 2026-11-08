# ADR-0012 — Analytics pédagogiques local-first et explicables

## Décision
EduNova calcule prioritairement les analytics pédagogiques **sur l'appareil**, à partir des données déjà détenues localement : activité, quiz, flashcards, erreurs, planning, échéances et progression.

Le moteur est déterministe. Il n'utilise aucun LLM et ne consomme donc aucun crédit IA.

## Frontière de confidentialité
Les documents, réponses libres, conversations personnelles et extraits de cours ne sont jamais requis pour produire le tableau de bord.

Les snapshots journaliers de tendance sont locaux. Si une synchronisation d'agrégats est ajoutée plus tard, elle devra rester opt-in, minimale et indépendante du contenu documentaire.

## Interprétation
- Un score de préparation n'est **pas une prédiction de note**.
- Les niveaux de risque signifient uniquement « action de révision à prioriser ».
- Le moteur expose un niveau de preuve `limited / moderate / strong` et neutralise le momentum lorsque les données sont trop faibles.
- Les recommandations donnent toujours une raison et une action concrète.

## Coût
0 appel IA pour les calculs du LOT 10.

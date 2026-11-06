# ADR-0004 — Planning adaptatif déterministe et local-first

## Décision

Le planning d’EduNova est **déterministe, explicable et exécutable localement**. L’IA générative n’est pas autorisée à décider seule des priorités quotidiennes.

## Motivation

Le planning doit rester disponible hors connexion, peu coûteux et auditable. Les données nécessaires (horaire, évaluations, progression, erreurs, flashcards, disponibilités) existent déjà localement.

## Conséquences

- le même jeu d’entrées produit le même plan ;
- les règles de priorité sont testables ;
- un serveur peut calculer le même résultat, mais n’est pas requis pour le fonctionnement de base ;
- l’IA peut expliquer/reformuler le plan, jamais le rendre opaque ;
- les décisions utilisateur (épingler, reporter, terminer) ont priorité sur une replanification automatique.

# LOT 3 — Moteur pédagogique intelligent

Version cible : **0.4.0**

## Objectif

Transformer un contenu documentaire déjà analysé en objets pédagogiques réellement exploitables hors ligne : résumés sourcés, flashcards à répétition espacée, quiz corrigés, registre d’erreurs, historique de tentatives et signaux de préparation.

## Principes non négociables

1. **Source first** : tout contenu généré conserve ses références document/chunk/pages.
2. **IA remplaçable** : le domaine ne dépend d’aucun fournisseur.
3. **Pas de publication médicale automatique** : tout contenu médical généré reste `review_required` avant publication collective.
4. **Offline réel** : résumés, cartes, questions, erreurs et historique vivent dans SQLite/Drift.
5. **Explicable** : la préparation ne prédit jamais une note ; les poids et signaux sont audités.
6. **Erreurs actives** : une erreur ne disparaît pas après un seul succès chanceux ; deux réussites consécutives sont requises.
7. **Historique** : chaque tentative et réponse est persistée pour les statistiques futures.

## Backend livré

- `pedagogy/domain` : modèles et règles métier pures.
- répétition espacée déterministe et testable ;
- évaluation QCM simple/multiple, vrai/faux, numérique et texte ;
- registre d’erreurs et récupération ;
- readiness adaptatif avec repondération des signaux absents ;
- construction de contexte RAG borné avec provenance ;
- quality gate deterministic ;
- contrats de génération résumé / flashcards / quiz ;
- API de capacités, readiness, revue flashcard et évaluation quiz.

## Flutter livré

- schéma Drift v3 ;
- résumés ;
- flashcards et états de répétition ;
- questions ;
- tentatives et réponses ;
- registre d’erreurs ;
- jobs pédagogiques ;
- repository hexagonal ;
- scheduler local ;
- hub de cours premium ;
- session flashcards ;
- session quiz ;
- persistance des erreurs et tentatives ;
- routes dédiées depuis Mes cours.

## Ce qui reste volontairement derrière des ports

- fournisseur IA réel ;
- synchronisation serveur ;
- TTS cloud ;
- validation éditoriale back-office ;
- calcul de planning quotidien (LOT suivant).

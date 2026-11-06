# LOT 4 — Planning académique intelligent

Version cible : **0.5.0**

## Objectif

Faire d’EduNova un compagnon quotidien capable de transformer l’horaire, les évaluations, les erreurs, la progression et le temps disponible en un plan d’étude explicable et actionnable.

## Capacités livrées

### Domaine/backend
- horaire hebdomadaire ;
- détection de conflits ;
- évaluations et échéances ;
- priorité explicable selon proximité d’évaluation, préparation, erreurs, flashcards dues et cours du lendemain ;
- mode temps disponible 5/15/30/60 minutes ;
- mode urgence ≤36 h ;
- notifications locales planifiées J-3/J-1/H-3 ;
- replanification automatique après changement d’échéance ;
- parser conservateur d’horaire issu d’un OCR ;
- validation utilisateur obligatoire avant insertion d’un horaire détecté.

### Flutter/local
- Drift v5 ;
- tables horaire, événements, tâches du plan, préférences, intentions notifications, brouillons import ;
- plan du jour calculé depuis les vraies données locales ;
- écran Réviser premium ;
- écran Calendrier premium ;
- ajout manuel d’échéances ;
- ajout manuel d’un cours à l’horaire ;
- import texte OCR avec revue et contrôle des chevauchements ;
- outbox pour événements/horaire ;
- notifications enregistrées comme intentions locales avant branchement natif.

## Principes

1. L’algorithme reste explicable : chaque tâche affiche ses raisons.
2. Le score de préparation n’est jamais présenté comme une prédiction de note.
3. Une détection OCR d’horaire ne s’applique jamais silencieusement.
4. Le plan doit respecter le temps réellement disponible.
5. Les données principales restent utilisables offline.
6. Une modification d’échéance supprime et reconstruit les intentions de rappel concernées.

# LOT 4 — Durcissement production du planning académique

Version : **0.5.1**  
Statut : **moteur backend/local renforcé ; certification Flutter réelle encore obligatoire**.

## Pourquoi v0.5.1

Le moteur 0.5.0 savait prioriser une journée à partir des échéances et du niveau de préparation. L’audit de production a montré qu’un compagnon universitaire premium devait aller plus loin : raisonner sur la capacité réelle de l’étudiant, plusieurs jours, la fatigue, les prérequis, les reports et le périmètre réel d’une évaluation.

## Capacités ajoutées

### 1. Disponibilité réelle
- plages d’étude datées et timezone-aware ;
- niveaux d’énergie faible/moyen/élevé ;
- soustraction automatique des cours/occupations pour produire les créneaux libres ;
- élimination des fragments trop courts.

### 2. Charge cognitive et fatigue
- charge cognitive de 1 à 5 par tâche ;
- évitement des tâches lourdes dans une plage d’énergie faible ;
- durée maximale d’un bloc ;
- durée maximale de travail continu ;
- pauses automatiques ;
- limitation du nombre de matières et des changements de matière dans une journée.

### 3. Prérequis et ordre pédagogique
- dépendances entre tâches ;
- blocage d’une tâche avancée lorsque ses prérequis ne sont pas terminés ;
- les préparations d’évaluation peuvent imposer la couverture du cours avant le quiz/examen blanc.

### 4. Planification multi-jours
- horizon configurable 1–60 jours ;
- report automatique du travail non terminé ;
- détection de travail qui risque de dépasser son échéance ;
- calcul du volume encore non planifié.

### 5. Faisabilité
- comparaison minutes nécessaires / minutes réellement disponibles avant une échéance ;
- alerte explicite en cas de déficit ;
- aucune promesse de réussite ou prédiction de note.

### 6. Périmètre d’une interrogation/examen
- sections/chapitres concernés ;
- importance faible/normale/élevée/critique ;
- objectif de préparation ;
- estimation transparente de la charge ;
- génération déterministe des tâches : lecture, diagnostic, flashcards, erreurs, quiz, examen blanc ;
- possibilité d’un temps total imposé, redistribué réellement entre les tâches.

### 7. Replanification stable
- conservation des blocs terminés ;
- conservation des blocs épinglés par l’étudiant ;
- recalcul du reste sans écraser silencieusement l’historique ;
- journal de révisions du plan.

### 8. Reports et dette d’étude
- report explicite d’un bloc ;
- compteur de reports ;
- dette en minutes par matière ;
- augmentation explicable de la priorité d’une tâche trop souvent reportée.

### 9. Adhérence réelle
- minutes prévues vs minutes réellement étudiées ;
- taux de sessions terminées ;
- réduction automatique du budget quotidien si les plans récents sont irréalistes ;
- augmentation très prudente après plusieurs sessions réellement tenues.

### 10. Notifications
- optimisation déterministe : heures calmes, déduplication et plafond quotidien ;
- priorité aux changements urgents et rappels proches de l’échéance ;
- les intents restent séparés de l’adaptateur OS pour préserver l’architecture hexagonale.

## Persistance locale Drift v6

Nouvelles données :
- règles de disponibilité ;
- périmètres d’évaluation ;
- dette de planification ;
- révisions de plan ;
- blocs d’étude datés ;
- sessions réellement effectuées ;
- actions utilisateur (terminer, reporter, épingler).

Les préférences de planification contiennent désormais aussi :
- max travail continu ;
- durée de pause ;
- max matières/jour ;
- max changements de matière ;
- objectif de préparation ;
- horizon de planification.

## Invariants

1. Aucun bloc ne dépasse une plage disponible.
2. Le temps d’étude + pauses ne doit pas dépasser la capacité de la plage.
3. Une tâche avec prérequis non remplis n’est pas planifiée.
4. Une tâche cognitive lourde n’est pas imposée dans une plage explicitement faible.
5. Les reports augmentent la dette, ils ne disparaissent pas.
6. Un plan recalculé ne doit pas effacer une tâche terminée ou épinglée.
7. Les décisions restent explicables : chaque bloc conserve ses raisons.
8. Les données locales continuent de fonctionner hors connexion.

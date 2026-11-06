# LOT 10 — UI/UX maximal v0.11.1

## Intention
La page Analytics ne doit pas être une collection de graphiques décoratifs. Elle doit répondre successivement à quatre questions :
1. **Où en suis-je ?**
2. **Sur quoi se base cette lecture ?**
3. **Que dois-je faire maintenant ?**
4. **Pourquoi cette action est-elle proposée ?**

## Expérience premium
- Hero narratif avec momentum, série, jours actifs, minutes recommandées et fraîcheur des données.
- Niveau de preuve visible : `limited / moderate / strong` traduit en langage étudiant.
- KPI 7 jours avec comparaison à la semaine précédente.
- Timeline d'activité sur 14 jours, sans dépendance graphique tierce.
- Recommandations triées, expliquées, reportables et masquables.
- Priorité lisible, sans présenter un score numérique opaque.
- Cours à surveiller sous forme de cartes actionnables.
- Drill-down d'un cours en bottom sheet avec :
  - couverture du cours ;
  - maîtrise quiz ;
  - flashcards ;
  - récupération d'erreurs ;
  - erreurs encore ouvertes ;
  - flashcards en retard ;
  - temps étudié ;
  - échéance la plus proche.
- Méthodologie repliable et explicite.
- Carte de progression directement sur l'accueil.

## Responsive
- mobile : flux vertical, actions à une main ;
- tablette : KPI en 2 colonnes ;
- desktop/web large : KPI en 4 colonnes et recommandations/cours côte à côte ;
- largeur globale contrainte par `EduNovaPageBody`.

## Accessibilité
- `Semantics` sur hero, KPI et barres d'activité ;
- aucune information critique encodée uniquement par la couleur ;
- support du thème sombre via `ColorScheme` ;
- libellés textuels des tendances ;
- bottom sheet avec `useSafeArea` ;
- textes multi-lignes pour éviter les truncations agressives.

## Doctrine analytique
- aucune prédiction de note ou de réussite ;
- aucune IA payante ;
- données locales ;
- prudence quand le volume d'observation est limité ;
- une action commencée n'est pas marquée comme “terminée” automatiquement ;
- maximum 5 recommandations, maximum 2 par cours.

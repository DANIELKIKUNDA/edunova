# LOT 10 — Analytics pédagogiques & recommandations intelligentes

## Objectif
Transformer l'historique réel de l'étudiant en décisions utiles, sans produire de graphiques décoratifs ni de pseudo-prédictions scolaires.

## Sources locales
- activité des 14 derniers jours ;
- temps d'étude ;
- quiz 7 jours vs 7 jours précédents ;
- progression des cours ;
- erreurs ouvertes/récupérées ;
- flashcards maîtrisées et en retard ;
- adhérence au planning ;
- échéances prochaines ;
- sessions par cours.

## Sorties
- momentum global prudent ;
- comparaison temps d'étude et quiz ;
- jours actifs / streak ;
- adhérence au planning ;
- cours `Priorité / À consolider / Stable` ;
- préparation explicable avec renormalisation quand certains signaux manquent ;
- 3 à 5 recommandations maximum, diversifiées par cours ;
- actions : préparer une évaluation, récupérer les erreurs, quiz ciblé, flashcards, continuer le cours, alléger un planning irréaliste.

## Feedback
L'étudiant peut :
- faire l'action maintenant ;
- la reporter de 24 h ;
- la masquer.

Les feedbacks restent locaux dans le LOT 10.

## Historique
Drift v16 ajoute un snapshot journalier par cours afin de construire progressivement des tendances 30/90 jours sans dépendre du cloud.

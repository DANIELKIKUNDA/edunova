# LOT 18 — Assessment & Exam Simulation Engine — v0.19.1

## Objectif
Mesurer la préparation par des évaluations traçables, versionnées et explicables sans confondre score d'un examen blanc et certitude académique.

## Contrat industriel
- Questions QCU/QCM/vrai-faux/réponse courte/exercice, provenance SHA-256 et pages source.
- Les examens `approved_only` n'acceptent que des questions validées.
- Blueprint: durée, taille, seuil, randomisation contractuelle.
- Tentative: jeu de questions figé au démarrage, sauvegarde/reprise, marquage à revoir, optimistic locking.
- Correction: score, réussite, explication et pages source par question, agrégation par chapitre.
- Offline-first: le contrat de tentative est conçu pour être répliqué par la couche Sync existante; la certification multi-device reste machine.
- High-stakes: aucune question générée non approuvée n'entre silencieusement dans un examen.

## UI/UX Student Delight
Environnement sans distraction, timer, progression, palette, marquage, autosave/offline, confirmation avant remise, résultats avec explications et CTA de remédiation. `From Volcano Tech` discret.

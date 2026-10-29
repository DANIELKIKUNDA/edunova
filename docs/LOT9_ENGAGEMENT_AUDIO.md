# LOT 9 — Notifications intelligentes, audio/TTS et engagement

## Objectif
Donner à EduNova un comportement de compagnon quotidien utile sans devenir envahissant.

## Notifications locales
- intents persistés dans Drift ;
- J-3 / J-1 / H-3 pour les évaluations ;
- expiration, priorité, deep-link et déduplication ;
- filtre local par préférences ;
- heures calmes ;
- maximum quotidien ;
- reprogrammation au démarrage ;
- `inexactAllowWhileIdle` pour éviter d’exiger inutilement les alarmes exactes Android.

## Push distant
Le backend stocke les appareils push et fournit un adaptateur Firebase Admin. Il reste désactivé tant que `FCM_ENABLED` n’est pas explicitement activé en production. Le worker `scripts/dispatch_engagement_push.py` peut être exécuté par cron/systemd timer.

## Engagement
- objectif quotidien configurable ;
- activité réelle reconstruite depuis sessions, quiz, flashcards et blocs terminés ;
- streak local calculé sur les jours actifs ;
- fenêtre glissante de 7 jours ;
- streak-notifications désactivées par défaut ;
- agrégats serveur monotones pour résister aux retries réseau.

## Audio/TTS
- voix locale ;
- aperçu gratuit, audio complet Premium ;
- vitesse 0,75× à 2× ;
- reprise à la dernière position ;
- repères audio ;
- prétraitement scientifique des symboles ;
- aucun MP3 obligatoire à stocker côté serveur.

## Coûts
Les fonctions centrales du LOT 9 fonctionnent sans IA et sans génération audio cloud. Le push distant est optionnel. L’objectif est de conserver les coûts récurrents proches de zéro hors infrastructure générale.

# ADR-0011 — Engagement local-first, notifications sobres et audio TTS

## Décision
EduNova sépare strictement :
- **rappels personnels** (échéances, plan du jour, flashcards) : planifiés localement sur l’appareil ;
- **push distants** (nouveau contenu, information plateforme) : adaptateur FCM optionnel et désactivé sans configuration explicite ;
- **audio** : TTS local en priorité afin de limiter stockage, bande passante et coûts.

## Règles de qualité
1. maximum quotidien configurable, par défaut 2 ;
2. heures calmes avec fuseau/offset utilisateur ;
3. déduplication par clé métier ;
4. une notification plus prioritaire peut remplacer une notification moins importante ;
5. notifications de série/streak désactivées par défaut ;
6. aucune dépendance au push distant pour les rappels essentiels ;
7. le résumé audio complet est Premium, l’aperçu reste gratuit ;
8. progression audio, vitesse et repères sont persistés localement ;
9. les données d’engagement synchronisées sont des agrégats légers, pas un journal détaillé de lecture.

## Confidentialité
Les documents personnels, texte OCR et contenu audio local ne sont jamais envoyés au module Engagement. Seuls des agrégats (minutes, tâches, quiz, flashcards) peuvent être synchronisés.

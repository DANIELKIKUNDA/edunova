# LOT 3 — Production hardening (v0.4.1)

Ce durcissement clôt les lacunes identifiées lors de l’audit pré-LOT 4.

## Ajouts backend

- provenance par item généré (`source_indexes`) ;
- empreinte SHA-256 des sources + `generation_key` stable pour détecter le contenu périmé et dédupliquer les générations ;
- qualité déterministe des questions (doublons, options dupliquées, explication manquante) ;
- politique de visibilité : contenu partagé non publié interdit aux étudiants ;
- objectifs d’apprentissage et niveaux cognitifs ;
- estimation de maîtrise pondérée et sensible à la récence ;
- sélection adaptative des questions de pratique ;
- quiz mixtes : QCM simple, QCM multiple, vrai/faux, numérique et texte libre ;
- tolérance numérique absolue/relative ;
- variantes acceptées pour texte libre ;
- API mastery + classement de pratique ;
- tous les tests historiques conservés.

## Ajouts Flutter/local

- schéma Drift v4 ;
- objectifs d’apprentissage et maîtrise locale ;
- métadonnées de portée contenu personnel/plateforme ;
- historique de chaque revue flashcard ;
- session quiz reprenable après fermeture/crash ;
- télémétrie de réponse prévue sans dépendre du serveur ;
- événements pédagogiques écrits dans l’outbox offline-first ;
- évaluateur local pour les cinq types de questions ;
- interface quiz multi-types ;
- progression de session persistée.

## Règles renforcées

1. Un contenu plateforme généré par IA n’est jamais visible publiquement tant qu’il n’est pas `PUBLISHED`.
2. Un contenu personnel peut rester visible au propriétaire même en `REVIEW_REQUIRED`, avec traçabilité des sources.
3. Une modification de la source produit une nouvelle empreinte ; les artefacts antérieurs sont détectables comme anciens.
4. Une question générée doit avoir une provenance itemisée et une explication.
5. Les événements offline pédagogiques doivent pouvoir être synchronisés sans perte.
6. Une session de quiz ne doit pas être perdue au redémarrage.

## Certification

- Backend Python : **48/48 PASS**.
- `python -m compileall` : PASS.
- Flutter : certification SDK réelle toujours obligatoire avant `CLOSED`.

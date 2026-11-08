# LOT 3 — Matrice d’acceptation

## Domaine/backend — certifié dans l’environnement ChatGPT

- [x] flashcard AGAIN remet la carte à J+1 et incrémente le lapse ;
- [x] HARD/GOOD/EASY modifient intervalle et facteur de facilité ;
- [x] QCM simple évalué ;
- [x] QCM multiple partiellement scoré et pénalisé en cas de sélection erronée ;
- [x] réponse numérique avec tolérance ;
- [x] tentative agrégée ;
- [x] incohérence nombre questions/réponses rejetée ;
- [x] erreur récupérée après deux réussites ;
- [x] nouvel échec réinitialise la récupération ;
- [x] readiness repondère les signaux absents ;
- [x] aucun score sans signal ;
- [x] contexte RAG garde la provenance ;
- [x] budget contexte respecté ;
- [x] gros chunk borné ;
- [x] source vide refusée ;
- [x] contenu médical forcé en revue humaine ;
- [x] contenu sans source interdit ;
- [x] contenu non médical propre peut être approuvé ;
- [x] génération résumé sourcée ;
- [x] génération flashcards sourcée ;
- [x] génération quiz valide 4 options / 1 réponse ;
- [x] API capabilities ;
- [x] API readiness ;
- [x] API flashcard review ;
- [x] API quiz evaluation ;
- [x] tous les tests historiques LOT 0-2 restent verts.

Résultat actuel : **48/48 tests Python PASS**.

## Flutter — à certifier sur SDK réel

- [ ] `flutter pub get` ;
- [ ] `dart run build_runner build --delete-conflicting-outputs` ;
- [ ] migration Drift v2 -> v3 ;
- [ ] `flutter analyze` = 0 erreur ;
- [ ] `flutter test` = PASS ;
- [ ] navigation Mes cours -> hub pédagogique ;
- [ ] résumés offline ;
- [ ] flashcard reveal + 4 ratings ;
- [ ] persistance d’un état flashcard après redémarrage ;
- [ ] quiz avec correction ;
- [ ] mauvaise réponse apparaît dans Mes erreurs ;
- [ ] deux bonnes réponses successives récupèrent l’erreur ;
- [ ] tentative quiz persistée ;
- [ ] mode avion : résumés/flashcards/quiz téléchargés restent utilisables ;
- [ ] Android : build debug ;
- [ ] Windows : build debug ;
- [ ] Web/PWA : build web ;
- [ ] iOS : certification ultérieure sur macOS cloud.

**Règle : LOT 3 n’est `CLOSED` qu’après cette certification Flutter.**


## Hardening pré-LOT 4

- [x] provenance par item généré ;
- [x] empreinte des sources / generation key ;
- [x] anti-doublons questions/options ;
- [x] politique visibilité personal/platform ;
- [x] objectifs d’apprentissage + mastery ;
- [x] pratique adaptative ;
- [x] quiz cinq types ;
- [x] tolérance numérique relative ;
- [x] variantes texte libre ;
- [x] historique flashcards local ;
- [x] quiz reprenable ;
- [x] événements pédagogiques dans outbox.

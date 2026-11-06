# EduNova — Phase 15 : clôture backend locale v0.50.7

**Date : 15 octobre 2026**  
**Base canonique vérifiée :** `EduNova_v0.50.6_RC_PHASE15_TEMPORAL_ARCHIVE_PRIVACY.zip`  
**SHA-256 vérifié de la base :** `4842a0b65596ad5a843ff66d85107ada45cc181c280c7e6d035f07c5a3118c1e`  
**Décision :** Phase 15 **CLÔTURÉE fonctionnellement au niveau backend local** après régression finale 889/889 PASS. **Ni certification de production, ni anonymisation absolue.**

## Historique conservé

Les checkpoints v0.50.0 à v0.50.6 ont consolidé le périmètre existant d'intelligence institutionnelle : indicateurs et alertes non prescriptives, surveillance de la complétude et traçabilité des sources, comparaison inter-périodes avec contrôle des participants, petits groupes et complément hiérarchique, cohortes qui se chevauchent, interfaces historiques/CSV, archives v4 temporisées. Les phases 0–14, gradebook, jury, Student Success et données individuelles ne sont pas réécrits.

## Diagnostic de reprise v0.50.6

Trois contournements subsistaient sur le périmètre des agrégats :

1. **Tableaux vivants :** la même route pouvait publier un taux avant et après une modification des notes ou de la composition d'une cohorte. Comparer les deux réponses constituait un canal d'inférence temporelle malgré les seuils de population.
2. **Archives :** masquer toutes les archives sauf la plus récente **ne retirait pas** les taux déjà diffusés lorsque cette archive était l'ancienne plus récente. Deux consultations successives pouvaient donc exposer deux états. Le paramètre de période ou le `limit=1` pouvait également réafficher une archive non contrôlée vis-à-vis des autres périodes.
3. **Intégrité :** la preuve HMAC v4 engageait la population mais **pas le payload statistique**. Une personne ayant accès à la base pouvait modifier le contenu et recalculer son SHA-256 public sans disposer de la clé HMAC.

## Correctifs implémentés

**A. Contrat de publication vivante v1 — migration SQL 0085.** Nouvelle table `institutional_analytics_live_releases`, clé primaire `(institution_id, scope_key)` avec première date et HMAC HMAC-SHA-256 de la projection publiée **et de la composition de la population**. Le serveur signe un engagement canonique et une nonce aléatoire de 192 bits. Les comptes étudiants, notes brutes et taux ne sont pas conservés dans cette table. Lorsqu'une statistique étudiante a déjà été divulguée pour un périmètre, la même population et la même projection sont exigées pour toute republication de ce périmètre. Un changement de barème, de note, de population ou une altération de l'engagement entraîne une **suppression intégrale** des taux, effectifs, dénominateurs, couvertures, empreintes et alertes. Les routes JSON, enseignant, CSV et tableaux décisionnels réutilisent ce contrat ; un index unique garantit que deux premières publications concurrentes ne peuvent pas créer deux lignes pour un même périmètre. L'absence de migration/clé provoque une décision fail-closed sur ces publications, et non une publication non protégée.

**B. Normalisation de périmètre.** Une requête sur un enseignement ou une cohorte sans identifiant de période et une requête équivalente avec sa période d'appartenance partagent un engagement temporel ; l'omission de `academic_period_id` ne réarme donc pas le droit à une première publication. Le ledger est également partitionné par institution.

**C. Archives contractuelles v5.** Une nouvelle capture comporte désormais **deux** engagements authentifiés : HMAC de population et HMAC de contenu public contextualisé par université + nonce, avec SHA-256 descriptif du contenu stocké. La lecture recalcule les deux engagements. Recalculer le SHA-256 après avoir falsifié les résultats n'est plus suffisant. Les archives v1–v4 restent conservées comme preuves historiques, mais sont **non diffusables par l'API gouvernée** faute d'engagement v5 validable.

**D. Première archive seulement.** Pour un périmètre institutionnel, une seule archive peut être consultée : **l'archive la plus ancienne**, à condition que la population actuelle soit identique et que son intégrité soit vérifiée. Toute capture ultérieure reste masquée, même via `limit=1`, période différente ou endpoint de comparaison. Le contrôle d'archive antérieure ne dépend jamais de la pagination contrôlée par le client.

**E. Régression adversariale.** Nouvelles vérifications contre : modifications des notes après consultation ; rotation à effectif inchangé ; corruption de clé/engagement ; clé serveur renouvelée ; inscriptions étrangères ; contournement du filtre période ; comparaison historique ; recalcul frauduleux de SHA-256 de contenu ; refus RBAC étudiants ; refus d'exposition CSV, tableaux et alertes après évolution de source.

## Restrictions de fonctionnalité explicites

Le gel **première publication / premier instant** est volontairement conservateur. Si une statistique vivante déjà publiée varie, la publication de la nouvelle valeur est **bloquée**, non « actualisée ». Ce checkpoint ne propose pas de bouton de remise à zéro car effacer un ledger pourrait permettre la divulgation par comparaison avec une ancienne réponse. Toute future republication nécessitera une politique de groupes disjoints/budget de confidentialité gouvernée, documentée et testée. De même, la seule archive v5 montrable est la première, pas la plus récente. Les utilisateurs peuvent toujours consulter des indicateurs non diffusables sous forme de statuts sans valeurs sensibles.

## Limites NON certifiées (transversales / infrastructure)

- **Protection générale contre les attaques par requêtes multi-périmètres non démontrée.** Des cellules partiellement chevauchantes, interrogées en parallèle et/ou depuis plusieurs rôles, peuvent conserver un risque d'inférence. Les protections statiques hiérarchiques et de cohortes proches réduisent ce risque, mais ne constituent pas une démonstration de confidentialité différentielle.
- **Atomicité PostgreSQL réelle et transactions concurrentes non certifiées.** L'extraction des sources, des populations et l'enregistrement de l'engagement reposent sur des transactions séparées ; modification concurrente et délais d'observation sont à éprouver sur PostgreSQL avec isolation choisie et charge réaliste. Le contrat SQL primaire unique est présent mais son comportement en charge réelle n'a pas été éprouvé.
- **Clé secrète :** la variable `INSTITUTIONAL_ANALYTICS_HMAC_SECRET` doit être stable et sécurisée (ou JWT_SECRET utilisé par repli historique). Sa rotation sans plan de re-signature rend les publications passées indisponibles ; ce mécanisme n'est pas une signature électronique qualifiée.
- **Historique déjà exporté :** rien ne peut effacer les copies téléchargées précédemment.
- **Lignée pédagogique ancienne :** les anciens agrégats non prouvés restent masqués et non présentés comme certifiés.
- **Scalabilité :** les grands volumes, indices PostgreSQL réels, latences, Redis, workers, stockage objet, compilation Flutter/mobile et appareils physiques n'ont pas été certifiés ici.
- **Audit structurel 17/17 :** contrôle de présence des contrats, pas une preuve de robustesse ou de sécurité de production.

## État des certifications

| Axe | État |
|---|---|
| Code Python/FastAPI existant modifié | Oui |
| Nouvelle migration versionnée | `0085` |
| Isolation/permissions | Tests SQLite + service (voir preuves) |
| Régression backend locale | **889/889 PASS**, voir `TEST_EVIDENCE_PHASE15_v0.50.7.txt` |
| Compilation Python | Voir preuves |
| Structure/dépendances Git | Audit statique seulement |
| PostgreSQL, Redis et stockages réels | **NON EXÉCUTÉ** |
| Flutter / Android / iOS / équipements réels | **NON EXÉCUTÉ** |
| Certification de production / juridique | **NON EXÉCUTÉ** |

## Décision de passage

**Phase 15 — développement fonctionnel backend local : CLÔTURÉ après 889/889 tests PASS.** Le périmètre n'est **pas déclaré totalement anonyme ni certifié production**. Les engagements de confidentialité transversaux et les tests sur infrastructure réelle restent des obligations des phases 20–24 et ne peuvent être qualifiés de résolus ici. Phase 16 non modifiée dans ce checkpoint. Aucun nouveau chantier parallèle n'a été introduit.

### Reprise et transparence des tests

Une première tentative de régression globale a échoué partiellement après lancement concomitant d'une suite ciblée : les deux processus utilisaient le même fichier SQLite de test, supprimé et recréé par `conftest.py`, d'où de nombreux messages `attempt to write a readonly database`. Un test de lineage ancien attendait la republication d'un taux modifié ; son contrat a été adapté à la **nouvelle exigence de gel**, en maintenant une vérification positive du recalcul brut côté dépôt. Le test des archives anciennes a aussi été ajusté pour la nouvelle règle **première archive visible**. Après stabilisation, la régression globale a été relancée **seule**, intégralement et sans reprise partielle : **889/889 PASS en 157,48 s, code 0**. Les journaux initiaux ne prouvent pas une régression réussie ; seul le journal final constitue la preuve de référence.

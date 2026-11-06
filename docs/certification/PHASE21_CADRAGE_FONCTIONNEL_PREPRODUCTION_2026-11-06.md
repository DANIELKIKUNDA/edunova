# EduNova — Phase 21 : certification fonctionnelle et préproduction

**Démarrage :** 6 novembre 2026  
**Base Git :** `import/edunova-v0.57.12` à `a7407415536ead5e16b633ff9adda93f4750ef7b`  
**Branche de travail :** `codex/phase21-certification-fonctionnelle-preproduction`  
**Statut :** CADRAGE — aucune preuve de Phase 21 obtenue par le présent document  
**Interdictions :** aucun déploiement en production, aucune transaction réelle, aucun secret dans Git, aucune fusion vers `main` ou la branche de base sans autorisation explicite.

## 1. Baseline réelle et limites de la Phase 20

La PR #2 est fusionnée. Les six jobs du workflow Phase 20 (PostgreSQL 16, Android APK, Windows, Linux, iOS **simulateur non signé** et Web Playwright) ont réussi sur la révision `01e1b6582c7df3e6d6e1065854eca1af939b79b1`. Les contrôles CI/sécurité/Phases 16, 17 et 19 étaient également verts après les derniers correctifs. Les contrôles CI ordinaires sur la branche d'import après fusion ont été relancés avec succès. Ces preuves ne valident **pas** automatiquement une distribution publique.

Les quatre scénarios Playwright Phase 20 portent sur le démarrage, le rendu mobile, la continuité d'une application déjà ouverte pendant une coupure réseau, et une limite de transfert. Ce ne sont pas des preuves de parcours de bout en bout utilisateur/serveur/DB, de synchronisation hors ligne complète, de paiement effectif ou de déploiement.

**Sécurité de publication :** l'APK release existant utilise actuellement une **clé debug**. L'application iOS est pour simulateur, sans archive signée pour iPhone. Ne pas qualifier ces artefacts de « prêts pour les stores ».

## 2. Objectif de la Phase 21

Obtenir, par scénarios automatisés reproductibles et preuves GitHub, une validation des flux **réels** des étudiants et administrateurs avec backend/API, PostgreSQL, navigateur Flutter et, lorsque possible, build Android. Corriger les défauts prioritaires, documenter les dépendances externes avant une éventuelle préproduction contrôlée.

## 3. Critères de recette à implémenter et certifier

| Priorité | Parcours / menace | Critère d'acceptation observable |
| --- | --- | --- |
| P0 | Identité, session et rôles étudiant/admin | Connexion, refus des accès non autorisés, déconnexion, expiration/révocation et persistance contrôlée; assertions côté API et interface |
| P0 | Multi-tenant / université et campus | Jeux de données A/B; impossible de lire, modifier ou exporter des ressources du tenant B via tenant A, y compris identifiants forgés et cache |
| P0 | Cours privé PDF/OCR → document traité → résumés/flashcards/quiz | Tester avec un PDF synthétique non personnel, un vrai traitement ou une frontière de fournisseur explicitement simulée; vérifier confidentialité, origine des contenus, erreurs et suppression |
| P0 | Offline / reprise et synchronisation | Écriture locale hors réseau, file conservée, reprise, idempotence et absence de duplication/effacement après reconnexion; scénario utilisateur + API/DB |
| P0 | Premium et Mobile Money | Simulation/sandbox seulement: attente, succès authentifié, échec, doublons, webhook falsifié, retour tardif, éventuelle compensation; aucune transaction réelle |
| P0 | Autorisations administration/editorial | Séparation Owner/Editor/Reviewer/Publisher, refus d'auto-approbation ou publication sans garde-fous selon règles métier |
| P1 | Restauration / migration PostgreSQL | Sur base éphémère: migrations sur base vierge, restauration d'un jeu de test, invariants, intégrité et retour arrière documenté |
| P1 | Performance / UI sur profil mobile modeste | Budget de chargement et erreurs console, lisibilité, débordements et capture d'écrans; ne pas assimiler l'émulation navigateur à un appareil physique |
| P1 | Préparation Android/iOS et release | Traçabilité version/commit/SHA-256/artefact; modèle de signature via secrets hors dépôt et procédure de signature sécurisée; certification réelle différée sans clés et appareils |

Chaque test qui dépend d'un tiers (Mobile Money, fournisseurs IA, Firebase, stores) doit distinguer **mock/contrat**, **sandbox** et **preuve réelle**. Pas de résultats « PASS » inférés à partir d'une compilation ou d'un test superficiel.

## 4. Exécution Cloud-First et maîtrise des coûts

1. Partir de cette branche de travail; la PR reste **brouillon** contre `import/edunova-v0.57.12`.
2. Inventorier les parcours et tests existants : `services/api/app/modules/identity`, `commerce`, `subscriptions`, `payment_gateway`, `ingestion`, `document_engine`, `sync`, `apps/mobile/lib/src/features`, `apps/admin`. Réutiliser les fixtures et tests existants avant d'ajouter de nouveaux doubles.
3. Implémenter des tests E2E avec véritables assertions métier et persistance PostgreSQL, environnement de test éphémère, comptes synthétiques et backend démarré en CI. Éviter tout service payant par défaut.
4. Organiser les CI en couches : analyses et tests rapides en PR; suites PostgreSQL/E2E métiers à la demande ou sur changement ciblé; compilations Windows/macOS/Android et scans lourds à jalon/release, avec annulation des runs obsolètes.
5. Conserver artifacts (JUnit, rapport Playwright, captures, logs expurgés, hashes et matrice de preuves) et versionner le rapport final avec le **SHA exact** testé.
6. Réaliser une revue contradictoire et documenter les P0 ouverts, dépendances de sécurité, limitations des mocks et tests non exécutés.

## 5. Conditions de sortie / GO–NO GO

La Phase 21 ne sera déclarée « fonctionnellement certifiée » que si :
- tous les parcours P0 déclarés dans le périmètre sont démontrés et verts sur le commit final ;
- isolement multi-tenant et contrôles d'accès adversariaux sont verts ;
- tests backend, Flutter, PostgreSQL, E2E et sécurité concernés sont verts ;
- les preuves sont téléchargeables et identifiées par commit; tout résultat non exécuté est marqué **NON VÉRIFIÉ** ;
- aucune régression critique ou faille de paiement/autorisation n'est ouverte.

**GO pour préparation de pilote** ≠ **GO pour production/stores**. Toute publication réelle exige en plus secrets/identifiants valides et non exposés, signature appropriée, conditions légales et bancaires, plan de restauration, tests sur appareils physiques et décision explicite du propriétaire.

## 6. Premier lot de travail

- **21.A — audit de couverture et matrice de traçabilité** des chemins API/Flutter ↔ tests, en identifiant P0 manquants.
- **21.B — harnais E2E backend/PostgreSQL + Flutter Web** réaliste, preuves lisibles.
- **21.C — parcours sécurité/multi-tenant et offline/sync** avec cas négatifs.
- **21.D — paiement simulé/sandbox et documents privés** avec idempotence et confidentialité.
- **21.E — préproduction/release, performance, recette et rapport final.**

Le présent commit sert **uniquement à cadrer et ouvrir le travail**. Aucun livrable de développement ou certification Phase 21 n'est revendiqué.

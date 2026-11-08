# EduNova — Phase 21 : certification fonctionnelle finale

**Date de clôture :** 7 novembre 2026  
**Branche certifiée :** `codex/phase21-certification-fonctionnelle-preproduction`  
**Révision applicative testée :** `b13f9514810e3951e46458fde3085e6c2f6b7ed5`  
**GitHub Actions :** [EduNova Phase 21 Functional Certification — run 9](https://github.com/DANIELKIKUNDA/edunova/actions/runs/42374651724)  
**Verdict :** **CERTIFIÉE — GO POUR PRÉPARATION D'UN PILOTE CONTRÔLÉ**

## 1. Périmètre prouvé

| Domaine | Preuve automatisée | Résultat |
| --- | --- | --- |
| Identité et sessions | API réelle, PostgreSQL 16, connexion, révocation et refus du rejeu | **PASS** |
| Sécurité et synchronisation | Comptes multiples, isolement, gouvernance, reprise et intégrité de synchronisation | **PASS** |
| Documents privés et pédagogie | Ingestion, stockage privé, assistant contextualisé et contrôles éditoriaux | **PASS** |
| Premium et paiements | Passerelle simulée/sandbox, idempotence, durcissement et parcours commerce | **PASS** |
| Flutter mobile et administration | Analyse statique et contrats ciblés de données privées, offline, Premium et administration | **PASS** |
| Flutter Web E2E | Navigateur réel : Flutter Web → API → PostgreSQL, connexion acceptée et refus visible des identifiants invalides | **PASS** |
| Préparation release | Migrations sur base PostgreSQL vierge, compilation APK release, hash SHA-256 et contrôle d'absence de clés suivies par Git | **PASS** |

Les six jobs du workflow Phase 21 ont terminé avec succès sur la même révision. Les workflows de non-régression **EduNova CI**, **Security**, **Phase 16**, **Phase 17**, **Phase 19** et **Phase 20** ont également terminé avec succès sur cette révision.

## 2. Anomalie corrigée pendant la certification

Le premier scénario navigateur échouait parce que `fill()` modifiait le nœud DOM du champ de mot de passe Flutter Web sans propager la valeur au `TextEditingController`. La requête contenait donc un mot de passe vide et l'API répondait correctement `401 invalid_credentials`.

Le scénario utilise désormais une saisie clavier séquentielle, identique au chemin d'un utilisateur. Une seconde attente incorrecte a aussi été corrigée : sur une installation neuve, `/bootstrap` est transitoire et dirige normalement l'utilisateur authentifié vers `/onboarding`.

## 3. Traçabilité et preuves

- Révision testée : `b13f9514810e3951e46458fde3085e6c2f6b7ed5`.
- Exécution Phase 21 : `42374651724`, conclusion `success`.
- Les artefacts GitHub contiennent les rapports de tests, journaux expurgés, captures du parcours Web, APK release technique, hash de l'APK et manifeste de limitation de signature.
- La PR de certification cible uniquement `import/edunova-v0.57.12`, baseline de la Phase 20.

## 4. Limites maintenues explicitement

Cette certification autorise la préparation d'un pilote contrôlé. Elle ne constitue pas encore une autorisation de publication publique ou de mise en production commerciale :

- l'APK produit est un artefact technique et n'est pas signé avec une clé de store détenue par le propriétaire ;
- l'iOS signé sur appareil physique et la publication App Store ne sont pas vérifiés ;
- les paiements Mobile Money sont validés par simulation/sandbox, sans transaction réelle ;
- les fournisseurs externes d'IA, les contrats opérateurs, les obligations légales et les secrets de production restent hors de cette preuve ;
- une recette sur appareils physiques modestes, la restauration opérationnelle et la décision explicite du propriétaire restent requises avant production.

## 5. Décision

Tous les critères automatisés P0 intégrés au workflow de Phase 21 sont verts, aucune régression critique n'est ouverte et les preuves sont liées à une révision immuable.

**Phase 21 : CLÔTURÉE ET CERTIFIÉE.**  
**Décision : GO pour préparation d'un pilote contrôlé ; NO-GO maintenu pour publication stores/production tant que les limites ci-dessus ne sont pas levées.**

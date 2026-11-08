# EduNova — Phase 22 : certification finale de préproduction et pilote contrôlé

**Date de clôture :** 8 novembre 2026  
**Branche :** `codex/phase22-controlled-pilot-readiness`  
**Révision technique testée :** `ac8ec5f9c3fa9d5deb086f8cb6817231c4f6c75b`  
**Workflow Phase 22 :** [run 42459040740](https://github.com/DANIELKIKUNDA/edunova/actions/runs/42459040740)  
**Verdict :** **CERTIFIÉE TECHNIQUEMENT — GO POUR RECETTE PHYSIQUE SUPERVISÉE**

## 1. Résultats certifiés

| Contrôle | Preuve | Résultat |
| --- | --- | --- |
| Configuration et déploiement | Variables, secrets, CORS, stockage, IA et paiement contrôlés en mode fail-closed ; composition Docker rendue | **PASS** |
| Runtime de préproduction | Staging/préproduction utilisent les protections de production ; observabilité, migrations et version vérifiées | **PASS** |
| Sauvegarde et restauration | Migrations sur PostgreSQL 16, sauvegarde custom, hash, restauration isolée et donnée témoin vérifiée | **PASS** |
| APK pilote Android | Compilation release avec endpoint HTTPS, SHA-256, commit testé et frontière de signature consignés | **PASS** |

Les workflows **EduNova CI**, **Security**, **Phase 16**, **Phase 17**, **Phase 19**, **Phase 20** et **Phase 21** ont également terminé avec succès sur la même révision.

## 2. Correctifs et protections livrés

- l'API est liée à `127.0.0.1:8000` par défaut : la readiness locale fonctionne sans publier directement le port sur Internet ;
- le worker d'ingestion est désormais en lecture seule avec un `/tmp` dédié et toutes les capacités Linux supprimées ;
- le déploiement exécute un garde de configuration avant tout build ;
- les migrations utilisent un conteneur PostgreSQL client dédié et les fichiers SQL montés en lecture seule ;
- `staging` et `preproduction` utilisent Redis, migrations explicites, stockage S3 privé, secrets obligatoires, budget IA et scanner d'ingestion comme la production ;
- le fournisseur de paiement sandbox est autorisé uniquement en staging/préproduction, jamais en production réelle ;
- l'image API installe explicitement la version corrigée de `zlib1g` ; le scan Trivy HIGH/CRITICAL est vert ;
- les fichiers `.env.production`, `.env.staging` et `.env.preproduction` sont exclus de Git ;
- un runbook documente déploiement, sauvegarde, restauration, incidents, arrêt du pilote et recette physique.

## 3. Traçabilité

- Révision testée : `ac8ec5f9c3fa9d5deb086f8cb6817231c4f6c75b`.
- Phase 22 : run `42459040740`, quatre jobs sur quatre en succès.
- Les artefacts conservés incluent l'APK pilote, son SHA-256, le commit testé, la limite de signature, le schéma restauré et les preuves de sauvegarde/restauration.
- Aucun secret réel, paiement réel ou accès production n'a été utilisé.

## 4. Éléments volontairement non déclarés vérifiés

| Élément externe | Statut | Condition de levée |
| --- | --- | --- |
| Signature propriétaire Google Play | **NON VÉRIFIÉE** | clé détenue hors Git et procédure de signature du propriétaire |
| Installation sur appareils physiques | **NON VÉRIFIÉE** | recette signée sur les modèles réellement retenus, notamment appareils modestes |
| Domaine pilote HTTPS réel | **NON VÉRIFIÉ** | domaine, certificat et reverse proxy du propriétaire |
| Mobile Money opérateur réel | **NON VÉRIFIÉ** | contrat/agrégateur et environnement sandbox officiel, puis décision séparée pour le réel |
| Restauration du bucket objet externe | **PRÉPARÉE, NON EXÉCUTÉE** | identifiants et bucket isolé appartenant au propriétaire |
| Publication stores et conformité | **HORS PHASE 22** | comptes stores, documents légaux, politique de confidentialité et décision du propriétaire |

Ces limites ne sont pas des échecs techniques de la Phase 22. Elles constituent les entrées humaines et externes de la Phase 23.

## 5. Décision

Les protections, procédures et preuves automatisables de préproduction sont vertes et reproductibles. Aucun P0 technique ouvert n'a été observé dans le périmètre exécuté.

**Phase 22 : CLÔTURÉE ET CERTIFIÉE TECHNIQUEMENT.**  
**GO : démarrer la Phase 23 — pilote réel supervisé et recette sur appareils.**  
**NO-GO maintenu : publication publique ou paiements réels avant levée formelle des limites externes.**

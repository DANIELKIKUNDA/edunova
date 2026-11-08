# EduNova v0.50.5 — Phase 15 : fermeture des contournements des projections institutionnelles historiques

**Date : 15 octobre 2026**  
**Point de départ canonique :** `EduNova_v0.50.4_RC_PHASE15_PEER_COHORT_PRIVACY.zip`  
**SHA-256 du point de départ, recalculé :** `6ac66e9952e497b12f0ebdaaba3524f9286313f869bfef159ab34791798390e2`  
**Décision :** Phase 15 **EN COURS**, Phase 16 non engagée. Ce checkpoint concerne le **backend local** et ne constitue pas une certification d'exploitation.

## 1. Constat dans le code existant

Les contrôles de publication gouvernée introduits en versions v0.50.0–v0.50.4 (`decision_brief`, `executive_readout`) masquaient des taux et dénominateurs lorsque la population était trop faible ou qu'une cohorte présentait un recoupement à risque. En revanche, le module existant **Lot 27** exposait toujours des routes historiques parallèles, notamment :

- `/dashboard`, `/units/{unit_id}/dashboard`, `/signals` et `/export.csv` ;
- `/executive-report` et `/pedagogical-intelligence` ;
- `/snapshots` (création, lecture d'archives) et `/comparisons`.

Ces routes pouvaient publier directement les projections originales, leurs détails de comptage ou des archives créées avant le contrat de confidentialité. La vérification de l'accès des administrateurs de faculté n'était pas uniformément appliquée aux chemins historiques. Le calcul pédagogique historique agrégeait des tentatives rattachées à un cours sans preuve suffisante de correspondance à l'inscription active et à la cohorte. Il serait trompeur de déclarer ces anciens résultats anonymisés ou multi-tenant certifiés.

## 2. Modifications réelles

### 2.1. Contrat commun de divulgation, version 3

`InstitutionalAnalyticsService._legacy_governed()` applique les mêmes contrôles que les consultations gouvernées de Phase 15, plutôt que de retourner des projections brutes :

- autorisation **RBAC**, identité de l'université et validation des références de périmètre ;
- comptes **distincts d'étudiants actifs**, plancher de divulgation, contrôle du complément hiérarchique, recoupements de cohortes ;
- qualité de source et population effectivement contributrice pour les indicateurs gouvernés ;
- suppression à `null` des cellules bloquées, y compris population, taux, dénominateurs et comptes historiques détaillés ;
- absence de seconde lecture brute après le calcul du `decision_brief`, pour éviter de juxtaposer sous concurrence un indicateur vérifié et un dénominateur différent.

Le chemin enseignant est strictement limité à un enseignement pour lequel l'affectation est active et reprend les protections de petite population et de recoupement. Les responsables de faculté doivent préciser une unité de leur arborescence autorisée : l'accès global et aux unités sœurs reste interdit. Un administrateur extérieur ou un étudiant ne peut pas exploiter les routes.

Les champs JSON historiques utiles sont **conservés nominalement**, mais certains champs auparavant renseignés deviennent `null` lorsqu'aucune preuve de publication sûre n'existe. Cela constitue une **évolution du contrat de réponse**, à prendre en compte par les clients et exports. Les données SQL originales restent inchangées.

### 2.2. Exports, signaux et rapport exécutif

Le CSV reprend **exactement** les cellules filtrées selon le contrat des vues JSON ; il ne comporte plus d'autre chemin vers des compteurs ou taux bruts. Les signaux sont calculés uniquement à partir d'un taux effectivement publié. Le rapport exécutif historique utilise les mêmes KPI filtrés et signale `contract_version: 3`, sans régénérer des calculs pédagogiques non gouvernés.

### 2.3. Agrégations pédagogiques historiques non certifiées

L'ancien agrégateur `pedagogical_intelligence` est **volontairement neutralisé** dans la surface institutionnelle ancienne lorsque la provenance complète (tentative ↔ étudiant inscrit ↔ cours ↔ période ↔ université) ne peut pas être démontrée. Les valeurs sont `null`, le résultat indique `unverified_legacy_lineage` et aucune conclusion automatique n'est rendue. Il n'y a **pas** de suppression des tentatives en base, mais ce point constitue une restriction fonctionnelle explicite à reprendre avec un contrat de preuve vérifiable. Le moteur pédagogique canonique de Phase 14, distinct, n'a pas été réécrit.

### 2.4. Archives et comparaisons

- Les captures nouvellement créées sont issues d'un payload filtré et portent `metric_contract_version = 3`, dans une **colonne déjà existante**.
- Les captures historiques v1/v2, dont les contenus potentiellement sensibles sont déjà stockés en base, ne sont pas supprimées ni falsifiées ; leur lecture via le service expose uniquement les métadonnées, avec `payload: null` et `content_sha256: null`.
- Une archive v3 devient également non communicable lorsque les inscrits actifs du périmètre actuel n'atteignent plus le seuil ou les autres conditions de divulgation.
- Les comparaisons requièrent **deux** captures communicables v3 ; aucune différence numérique n'est rendue entre captures non fiables ou masquées.
- Création, liste et comparaison exigent des paramètres `scope_type`/`scope_id` cohérents et réappliquent l'autorisation. Les requêtes génériques « toutes les cohortes / tous les enseignements » sont refusées.

Le digest SHA-256 de capture est une **empreinte descriptive**, non une attestation signée et non une garantie d'immuabilité juridique.

### 2.5. Persistance et migrations

Modification du dépôt `SqlAlchemyInstitutionalAnalyticsRepository.save_immutable_snapshot()` : nouvel argument facultatif `metric_contract_version` (défaut conservateur `1` pour compatibilité de l'interface dépôt). Le service impose `3` pour les nouvelles captures gouvernées. Aucune nouvelle table ni colonne ; **aucune migration nécessaire**. Dernière migration déjà présente : **0084**.

## 3. Tests

- Régression avant changement : **837/837 PASS**, SQLite/SQLAlchemy local.
- Les dix tests Lot 27 demeurent, mais **sept assertions historiques** ayant pour effet d'exiger une publication devenue dangereuse sont actualisées pour vérifier au contraire le masquage, avec commentaires expliquant le changement de contrat. Aucun module métier ancien n'est effacé.
- **21 nouveaux cas de tests** de fermeture : populations de 1 et 5 étudiants, notes publiées valides, deux cohortes qui se chevauchent, comparaison par unité, enseignants, facultés, université étrangère, interdiction des portées ouvertes, archivage v1 et v3, changement d'inscriptions, lecture CSV, tests **FastAPI TestClient réels** sur les routes et statuts HTTP 200/403/422.
- Tests exécutés avec SQLite de test. Les tests HTTP utilisent une connexion SQLite mémoire partagée dans leur seule fixture (`StaticPool`) parce que TestClient exécute les routes dans un autre thread.

**Suite globale finale isolée : 858/858 PASS, exit 0, en 71.79 secondes.** Preuves : `TEST_EVIDENCE_PHASE15_v0.50.5.txt` et pièce jointe externe.

**Incident intermédiaire de banc de test :** une tentative de régression globale a coïncidé avec le lancement d'une autre session pytest ciblée. Le `conftest.py` du dépôt efface sa base SQLite de test au démarrage ; la deuxième session a donc invalidé le fichier utilisé par la première, entraînant des erreurs `attempt to write a readonly database`. Il s'agissait d'une collision du dispositif d'essai, pas d'un test fonctionnel vert. La régression finale est donc exécutée **seule**, sans aucun autre pytest concurrent. Le journal de l'essai incorrect n'est pas présenté comme une réussite.

## 4. Limites, risques résiduels et validation externe

1. **Consultations répétées / évolution des effectifs :** les contrôles recouvrent les relations statiques connues et la sécurité du **périmètre courant** lors de l'accès aux archives ; ils ne garantissent pas la résistance aux inférences temporelles, à toutes les unions arbitraires, à la collusion et aux compositions multiples. Pas de budget persistant de confidentialité différentielle.
2. **Instantané historique :** une archive v3 antérieure peut porter des valeurs de période précédente. Le recontrôle du périmètre présent ne garantit pas que les populations étaient identiques aux deux dates. Une analyse transactionnelle temporelle reste à concevoir et certifier.
3. **Pédagogie ancienne :** le service institutionnel historique refuse maintenant de publier des statistiques non vérifiables. Une future preuve canonique par tentative/étudiant/offering est nécessaire pour rouvrir ce chemin.
4. **Concurrence et performance :** les contrôles SQL de recoupement demandent encore une certification sur PostgreSQL réel, avec isolation transactionnelle, indexes et volumétrie représentative. La fenêtre entre `decision_brief` et autres sources et les mises à jour concomitantes ne sont pas garanties atomiques ici.
5. **Périmètre de routes :** ce checkpoint traite le service `institutional_analytics` du Lot 27 et les interfaces Phase 15 existantes ; il **ne prouve pas** l'absence de tous les autres chemins statistiques dans l'ensemble de la plateforme.
6. **Systèmes externes :** aucune compilation Flutter, aucun test PostgreSQL ou Redis réels, aucune validation du stockage objet, aucune certification appareil ni fournisseur externe n'est revendiquée.
7. **Notes officielles et gouvernance :** aucune note de gradebook, décision de jury ou dossier Student Success n'a été modifié ; les suggestions institutionnelles restent consultatives.

## 5. Décision

**EduNova v0.50.5 : checkpoint backend local accepté après régression finale 858/858 PASS, audit 17/17 PASS et compilation Python réussie.** La **Phase 15 reste ouverte** : prochaine priorité, reconstitution de la lignée canonique pour l'intelligence pédagogique historique, contrôle des risques de différenciation temporelle des archives et validation PostgreSQL transactionnelle lors de la phase prévue. La roadmap 0–26 reste inchangée.

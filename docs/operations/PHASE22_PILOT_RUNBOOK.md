# EduNova — Runbook du pilote contrôlé (Phase 22)

## 1. Autorisation et périmètre

Le pilote utilise uniquement des comptes et contenus synthétiques ou explicitement autorisés. Les paiements restent en sandbox. Aucun secret n'est stocké dans Git, dans l'APK ou dans les preuves CI.

Les rôles sont séparés : le responsable technique déploie et surveille ; le propriétaire autorise le groupe pilote, les appareils, le domaine HTTPS et les contrats externes.

## 2. Prévol obligatoire

1. Créer `.env.production` hors du dépôt avec des secrets générés aléatoirement.
2. Exécuter `docker compose -f docker-compose.production.yml run --rm config-gate`.
3. Vérifier que l'API est publiée uniquement sur `127.0.0.1:8000` et exposée aux utilisateurs par un reverse proxy HTTPS.
4. Tester `/v1/operations/live`, `/v1/operations/ready` et `/v1/operations/metrics` depuis le réseau d'administration.
5. Produire une sauvegarde PostgreSQL et objets, vérifier les hashes, puis restaurer dans un environnement isolé.
6. Conserver le SHA Git, le SHA-256 de l'APK et le résultat des contrôles dans le registre du pilote.

## 3. Déploiement contrôlé

- Utiliser un tag immuable et renseigner `RELEASE_TAG` et `DEPLOY_DIR`.
- Lancer `scripts/deploy_production.sh` depuis le serveur autorisé.
- Le déploiement doit s'arrêter avant build si la configuration est invalide.
- Les migrations s'exécutent dans le service `migrate`, jamais depuis l'image API minimale.
- La readiness doit devenir verte en moins de 60 secondes ; sinon le script appelle le rollback.

## 4. Sauvegarde et restauration

### PostgreSQL

- Sauvegarde : `DATABASE_URL=... BACKUP_DIR=... scripts/backup_postgres.sh`.
- Vérifier le fichier `.sha256` avant copie externe.
- Restaurer d'abord dans une base isolée avec `CONFIRM_RESTORE=RESTORE_EDUNOVA`.
- Vérifier identité, tenants, droits, documents, paiements sandbox et files de synchronisation avant toute restauration réelle.

### Objets privés

- Sauvegarde : renseigner `CONTENT_STORAGE_BUCKET` et `BACKUP_DIR`, puis exécuter `scripts/backup_object_storage.sh`.
- Restauration : utiliser un bucket de test et `CONFIRM_OBJECT_RESTORE=RESTORE`.
- Comparer le manifeste interne `SHA256SUMS` avant synchronisation.

## 5. Réponse aux incidents

| Gravité | Exemple | Action immédiate |
| --- | --- | --- |
| P0 | fuite potentielle, accès cross-tenant, webhook falsifié accepté | arrêter le pilote, révoquer les secrets concernés, préserver les journaux expurgés, informer le propriétaire |
| P1 | perte de données, restauration impossible, authentification indisponible | passer en maintenance, suspendre les écritures, restaurer dans un environnement isolé, décider rollback |
| P2 | performance dégradée ou fonction non critique indisponible | limiter le groupe pilote, ouvrir un diagnostic avec request ID, corriger au prochain jalon |

Ne jamais copier de jeton, mot de passe, document privé ou payload Mobile Money dans un ticket. Utiliser le `X-Request-ID`, l'heure UTC, le SHA de version et le rôle affecté.

## 6. Recette sur appareils physiques

Pour chaque appareil, consigner modèle, version Android, RAM, réseau, SHA-256 de l'APK et résultat :

- installation et première ouverture ;
- création/connexion/déconnexion et redémarrage ;
- import d'un PDF synthétique, quiz et suppression ;
- fonctionnement hors connexion puis synchronisation sans doublon ;
- paiement sandbox : attente, succès, échec et doublon ;
- lisibilité, navigation, mémoire, batterie et temps de réponse ;
- révocation de session depuis un second appareil ;
- désinstallation et absence d'accès résiduel aux données privées.

Cette recette demeure **NON VÉRIFIÉE** tant qu'un humain n'a pas signé les résultats sur les appareils réellement choisis.

## 7. Conditions d'arrêt du pilote

Le pilote est arrêté immédiatement en cas de fuite possible, isolement tenant contournable, perte non restaurable, secret exposé, paiement hors sandbox ou divergence entre APK installé et SHA approuvé.

Le passage à la Phase 23 exige : Phase 22 CI verte, restauration prouvée, APK traçable, domaine HTTPS opérationnel, secrets propriétaires injectés hors Git et recette physique signée.

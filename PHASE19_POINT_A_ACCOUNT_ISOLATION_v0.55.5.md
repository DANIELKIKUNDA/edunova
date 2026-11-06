# EduNova Phase 19 — Point A, checkpoint v0.55.5

## Décision d'architecture
Les projections SQLite sont globales et de nombreuses fonctionnalités (documents, lecture, quiz, cours, planification) n'ont pas de clé `accountId`. **Le multi-compte local n'est pas pris en charge.** Ce lot renforce un modèle *un seul propriétaire de données locales par installation*, sans supprimer ni transférer les données existantes. Il ne constitue PAS une migration multi-tenant des tables.

## Changements effectivement intégrés
- `SecureSessionStore` conserve `auth.localDataOwner` au-delà de la déconnexion, y compris lors de la migration d'une ancienne session.
- `save` refuse un autre `accountId` avant d'écrire les jetons, et `read` refuse une session incohérente avec le propriétaire.
- `ApiIdentityRepository` vérifie les propriétaires déjà enregistrés dans `localCloudSyncStates` **avant** de persister les sessions de connexion, d'inscription et de rafraîchissement.
- Le fournisseur Riverpod injecte la base SQLite dans le dépôt d'identité.
- Les protections existantes du dépôt de synchronisation v0.55.3 et v0.55.4 restent en place.

## Tests et réserves
- Backend synchronisation : **17/17 PASS**.
- SDK Flutter/Dart indisponible ici : compilation, analyse statique et tests Flutter **non exécutés**.
- Le marqueur sécurisé n'est pas une migration de toutes les tables. Une installation ancienne déjà déconnectée sans marqueur ni état de synchronisation reste un cas de migration à traiter. Les écritures dans le stockage sécurisé ne sont pas atomiques entre elles ; un double login simultané nécessite une protection supplémentaire.
- Pour certifier le point A au niveau final : tests Flutter sur connexion/déconnexion/reconnexion, changement de compte, installation historique, accès hors connexion et vérification des fichiers locaux ; décision produit explicite « compte unique par installation » ou véritable stockage distinct par compte.

**Statut : point A renforcé, mais non certifié final.** Ne pas passer automatiquement au point B en prétendant que l'isolation est complète.

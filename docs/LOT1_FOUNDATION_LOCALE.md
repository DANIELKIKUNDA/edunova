# LOT 1 — Fondation locale

## Objectif

Faire d’EduNova une application réellement local-first avant tout branchement IA, OCR ou paiement.

## Livré

- Profil académique persistant : faculté, programme, niveau, semestre, établissement facultatif.
- Bootstrap automatique : nouvel utilisateur -> onboarding ; utilisateur configuré -> accueil.
- Base locale Drift/SQLite avec tables : profil, documents personnels, cours, évaluations et outbox.
- Bibliothèque personnelle observable.
- Import local de PDF/images sur plateformes natives.
- Copie des documents dans l’espace privé de l’application.
- Métadonnées locales ; aucun upload automatique du document personnel.
- Classification : cours, interrogation, examen, exercice, notes, autre.
- Outbox offline-first : les événements de métadonnées sont mis en file pour une future synchronisation idempotente.
- Ports séparés pour dépôt de documents, fichiers privés et synchronisation.
- Tests métier Dart ajoutés (à exécuter après installation Flutter).

## Web/PWA

La base Drift Web est préparée. Le stockage binaire personnel PWA est intentionnellement laissé derrière `LocalDocumentStore` et sera branché sur OPFS dans le lot Web/offline. Il est interdit de contourner ce point en uploadant silencieusement les PDF personnels sur le backend.

## Génération Drift

Après `flutter pub get` :

```bash
dart run build_runner build --delete-conflicting-outputs
```

Le script `scripts/bootstrap_flutter.ps1` exécute désormais aussi cette étape.

## Non inclus dans LOT 1

- lecteur PDF complet ;
- OCR réel ;
- extraction de chapitres ;
- synchronisation serveur ;
- chiffrement local final ;
- OPFS Web ;
- IA ;
- paiement.

Ces éléments restent derrière les ports prévus et sont ajoutés dans les lots suivants.

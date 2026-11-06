# LOT 7 — Synchronisation cloud, multi-appareils et bibliothèque EduNova

## Objectif
Faire suivre l'étudiant entre Android, PWA et ordinateur sans transformer EduNova en cloud de fichiers personnels.

## Sync
- appareil enregistré avec plateforme + version application ;
- mutations idempotentes (`mutation_id`) ;
- version optimiste des objets modifiables ;
- conflits retournés avec version canonique ;
- progression de lecture fusionnée sans régression accidentelle ;
- événements quiz/review/session append-only ;
- tombstones pour suppressions ;
- snapshot bootstrap pour nouvel appareil ;
- pull incrémental par curseur ;
- isolation stricte par compte ;
- limites de taille et rate limiting ;
- résolution locale d'un conflit : garder cloud ou republier la version locale sur la dernière version canonique.

## Bibliothèque commune
Hiérarchie indépendante d'une université :
`faculté/domaine → programme → niveau → semestre → cours → version → ressources`.

Chaque cours possède une version active et un manifeste de ressources. Les ressources peuvent être gratuites ou Premium et autoriser ou non le hors-ligne. Les clés `storage_locator` ne quittent jamais le serveur ; le client reçoit un jeton HMAC court et opaque.

## Frontière de confidentialité
Sont explicitement local-only : PDF/photos personnels, OCR personnel, chunks personnels et conversations assistant personnelles. Le serveur Sync rejette ces types même si un client malveillant tente de les pousser.

## Mobile
Drift v11 ajoute : état cloud, file de mutations, versions canoniques, conflits, catalogue, versions, ressources et état des téléchargements. Profil, calendrier, horaire et préférences créent une mutation cloud dans la même transaction que l'écriture locale.

## Ce qui reste volontairement hors LOT 7
Le téléchargement binaire réel depuis R2/S3 n'est pas simulé : le manifeste et l'autorisation sont prêts, mais l'adaptateur stockage production sera certifié lorsqu'un bucket réel et ses clés seront disponibles.

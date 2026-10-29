# Baseline EduNova v0.8.0

Checkpoint LOT 7 construit sur v0.7.1.

## Ajouts structurants
- bounded context `sync` côté backend ;
- bounded context `library` côté backend ;
- push idempotent et versionné ;
- snapshot bootstrap + deltas par curseur ;
- conflits explicites et rejouables ;
- progression monotone ;
- append-only immuable ;
- rate limiting Sync ;
- catalogue EduNova indépendant de l'université ;
- cours et ressources versionnés ;
- manifestes freemium/Premium ;
- jetons de livraison HMAC courts sans exposition des clés de stockage ;
- Drift v11 et cache de bibliothèque ;
- synchronisation opportuniste au lancement/reprise ;
- résolution locale des conflits ;
- vrais cours EduNova dans l'écran `Mes cours` à la place des cartes de démonstration.

## État
- Backend : certifié ChatGPT.
- Flutter : code préparé, certification SDK réelle requise.
- R2/S3 binaire production : volontairement non simulé tant qu'un bucket réel n'est pas choisi/configuré.

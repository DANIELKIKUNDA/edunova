# ADR-0010 — Distribution de contenu et cache offline

## Décision
Les ressources EduNova partagées sont stockées dans un object storage S3-compatible (R2 recommandé) et livrées par **capabilités courtes**. Le petit VPS ne doit pas devenir le point de transit obligatoire des gros PDF/audio en production.

## Principes
- `storage_locator` ne quitte jamais le backend.
- Le manifeste fournit seulement un `delivery_token` court.
- Un endpoint de grant revalide l'accès (y compris Premium) et retourne soit une URL S3/R2 pré-signée, soit un proxy Range en développement.
- Les grants offline ne sont accordés qu'aux ressources `offline_allowed`.
- Taille et SHA-256 du catalogue sont comparés au stockage avant livraison lorsque le bucket expose le checksum.
- Les téléchargements sont reprenables (`Range`, `If-Range`, ETag) et vérifiés SHA-256 avant passage à l'état `ready`.
- Un changement d'ETag invalide le fichier partiel pour empêcher le mélange de deux versions.
- Android/iOS/Windows utilisent le stockage privé de l'application.
- Web/PWA conserve les ressources par chunks dans Drift/Web SQLite (OPFS lorsque disponible).
- Les fichiers personnels ne font jamais partie du cache nettoyable EduNova.
- Premium offline est contrôlé par l'entitlement local borné du LOT 5 ; conserver physiquement un fichier ne confère pas un droit d'accès permanent.

## Conséquence économique
En production, les gros octets passent directement du stockage objet au client. Le VPS gère l'autorisation et les métadonnées, pas la bande passante lourde.

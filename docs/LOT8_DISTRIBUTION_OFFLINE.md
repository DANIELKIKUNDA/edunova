# LOT 8 — Distribution de contenu & Offline sécurisé

## Objectif
Permettre à un étudiant de rendre des ressources EduNova réellement disponibles hors connexion, même avec un réseau instable, sans exposer les clés de stockage ni surcharger le VPS.

## Backend
- Module hexagonal `delivery`.
- Grant court lié au compte + ressource + expiration.
- Revalidation Premium au moment du grant.
- `purpose=offline|stream` ; offline interdit si la ressource ne l'autorise pas.
- S3/R2 presigned GET en production.
- Proxy local/dev avec `Accept-Ranges`, `206`, `Content-Range`, `ETag`.
- Single-range uniquement ; multi-range rejeté volontairement.
- Taille objet et checksum vérifiés avant grant.
- Rate limit sur les grants.
- Path traversal bloqué dans le storage local de développement.

## Mobile/PWA
- Drift v14.
- État de téléchargement enrichi : offset, total, ETag, checksum, erreurs, retries, pin, dernier accès.
- File persistante de téléchargements avec backoff et reprise au redémarrage.
- Téléchargement ressource ou cours complet.
- Refresh du manifeste à la reprise : les tokens courts ne sont jamais persistés comme droits durables.
- Vérification SHA-256 avant finalisation atomique.
- Si ETag change : suppression du partiel et redémarrage propre.
- Politique gros fichiers en Wi-Fi par défaut.
- Cache max 2 Go par défaut, modifiable plus tard dans l'UI.
- Nettoyage LRU : protège les éléments épinglés et, selon politique, les cours suivis.
- Écran « Contenus hors connexion » : taille utilisée, téléchargements, erreurs, épinglage et suppression.
- Android/Windows : fichiers privés app.
- PWA : chunks binaires Drift/Web SQLite.

## Frontière stricte
Le nettoyeur LOT 8 ne touche qu'aux ressources EduNova partagées. PDF, photos, anciennes interrogations et notes personnelles restent dans la bibliothèque privée du LOT 1/2.

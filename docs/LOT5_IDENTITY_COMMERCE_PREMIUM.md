# LOT 5 — Identity, Premium, Mobile Money et quotas IA

## Objectif
Industrialiser la monétisation d'EduNova sans dépendre des stores, tout en protégeant comptes, paiements et fonctionnement offline.

## Backend
### Identity
- compte e-mail ou téléphone ;
- mot de passe Argon2id ;
- access token JWT 15 min ;
- refresh token opaque 30 jours, hashé côté serveur et rotatif ;
- replay d'un refresh token révoqué refusé ;
- token versioning prêt pour révocation globale ;
- rate limiting inscription/connexion ;
- audit des connexions et créations.

### Commerce
- catalogue serveur de plans ;
- prix Premium en CDF configurable ;
- checkout idempotent ;
- états paiement explicites ;
- callback signé obligatoire ;
- montant/devise/relation fournisseur vérifiés ;
- webhook inbox anti-replay ;
- renouvellement anticipé conserve les jours restants ;
- reçu unique par paiement ;
- reversal traité ;
- audit paiement ;
- sandbox interdit en production.

### Quotas IA
- essai gratuit : 3 crédits ;
- quota Premium cyclique ;
- crédits achetés séparés et persistants ;
- solde négatif impossible.

### Offline Premium
Le serveur émet un snapshot d'entitlement mis en cache localement. Le lease offline est volontairement borné à 72 h et ne dépasse jamais la date réelle d'expiration Premium.

## Mobile
- tokens dans `flutter_secure_storage`, jamais SQLite ;
- Drift v7 : entitlement, paiements, reçus, usage IA ;
- écran login/register ;
- écran Premium avec offre serveur, Mobile Money, suivi de paiement et reçus ;
- fournisseurs de paiement découverts dynamiquement ;
- ouverture redirect/USSD supportée ;
- mode local reste utilisable sans compte jusqu'aux fonctions nécessitant sync/Premium.

## Persistance serveur
PostgreSQL : accounts, refresh_sessions, payment_intents, entitlements, ai_wallets, receipts, webhook_inbox, audit_events.

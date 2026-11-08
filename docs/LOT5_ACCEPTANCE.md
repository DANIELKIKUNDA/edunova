# LOT 5 — Critères d'acceptation

## Cœur serveur
- [x] compte sécurisé Argon2id
- [x] JWT court + refresh rotatif
- [x] checkout idempotent
- [x] double webhook sans double activation
- [x] montant falsifié refusé
- [x] renouvellement anticipé sans perte de jours
- [x] reversal géré
- [x] reçu unique
- [x] quota IA non négatif
- [x] quota cyclique séparé des crédits achetés
- [x] entitlement offline borné
- [x] rate limiting
- [x] audit critique
- [x] sandbox désactivé en production
- [x] PostgreSQL migration de référence

## Mobile — à compiler/certifier sur SDK réel
- [ ] Drift v6 → v7
- [ ] secure storage Android
- [ ] secure storage Web/PWA
- [ ] login/register
- [ ] écran Premium
- [ ] checkout Mobile Money sandbox
- [ ] polling paiement / reprise après fermeture
- [ ] receipts offline
- [ ] expiration entitlement offline
- [ ] Android build
- [ ] Web/PWA build
- [ ] Windows build

## Mobile Money production — volontairement OPEN
- [ ] fournisseur/agrégateur choisi et contrat marchand actif
- [ ] adaptateur officiel implémenté selon documentation fournisseur
- [ ] signature callback certifiée
- [ ] paiement réel accepté
- [ ] paiement refusé
- [ ] expiration
- [ ] callback retardé
- [ ] callback dupliqué
- [ ] réseau coupé pendant confirmation
- [ ] montant/devise incorrects
- [ ] rapprochement/reconciliation
- [ ] reversal/remboursement

Le lot n'est **pas CLOSED production** avant ces validations externes.

# LOT 5 — Production hardening v0.6.1

## Objectif
Porter Identity + Commerce d'un flux fonctionnel à un socle financier exploitable en production sous réserve de certification du vrai fournisseur Mobile Money.

## Renforcements
- ledger `subscription_grants` : chaque paiement Premium crée un droit réversible indépendamment ;
- reversal du dernier renouvellement => retour à la période payée précédente, pas suspension arbitraire de tout le compte ;
- consommation IA transactionnelle avec verrou de ligne ;
- conflit d'idempotency détecté si une même clé est réutilisée avec un autre plan/téléphone/fournisseur ;
- événements de paiement tardifs terminaux ne rétrogradent pas un paiement déjà settled ;
- sweep des checkouts expirés ;
- gestion des appareils : liste, révocation d'une session, logout-all ;
- détection de réutilisation d'un refresh token roté => révocation globale + bump `token_version` ;
- changement de mot de passe => révocation globale et réauthentification ;
- récupération de compte avec code temporaire, 5 essais, expiration 10 min, anti-enumération ;
- provider SMS/e-mail derrière un port ; désactivé en production tant qu'un fournisseur n'est pas configuré ;
- UI Flutter Sécurité/Appareils + récupération de compte ;
- migration SQL ajoutant `subscription_grants` et `recovery_challenges`.

## Certification ChatGPT
- `python -m compileall -q app` : PASS
- `pytest -q` : 115/115 PASS

## Restent OPEN
- vrai agrégateur Mobile Money : KYC, clés, signature, sandbox puis transactions réelles ;
- provider SMS/e-mail de récupération en production ;
- Flutter SDK réel : build_runner/analyze/test/build Android/Web/Windows/iOS cloud.

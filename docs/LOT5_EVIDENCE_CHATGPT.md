# LOT 5 — Preuves exécutées dans l'environnement ChatGPT

## Exécuté
- `pytest -q` backend complet : **107/107 PASS**.
- `python -m compileall -q app` : PASS.
- parcours API sandbox couvert : register → checkout → webhook signé → entitlement Premium → quota IA → reçu.
- tests de sécurité/métier : idempotence, replay webhook, montant falsifié, renouvellement anticipé, reversal, refresh token replay, Argon2, quota négatif, lease offline, persistence SQLAlchemy, rate limit, pack IA.

## Non exécuté ici
Flutter SDK absent : génération Drift v7, `flutter analyze`, `flutter test`, Android/Web/Windows builds restent à certifier sur machine réelle.

## Externe volontairement non certifié
Aucun fournisseur Mobile Money production n'est codé sans documentation/credentials validés. Le sandbox est explicitement désactivé en environnement `production`. La certification réelle suivra le choix de l'agrégateur et le KYC marchand.

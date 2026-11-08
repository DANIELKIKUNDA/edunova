# LOT 5 — Certification machine

## Backend
```bash
cd services/api
python -m compileall -q app
pytest -q
```
Attendu : 107 tests ou plus, 0 échec.

## Flutter
```bash
cd apps/mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter build apk --debug
flutter build web
flutter build windows --debug
```

Tester ensuite : création compte, login, refresh, Premium offline, migration Drift v7, paiement sandbox, fermeture/réouverture pendant paiement, expiration 72 h du lease offline.

## Production Mobile Money
Ne jamais utiliser le sandbox en production. Configurer l'adaptateur fournisseur réel uniquement après KYC/contrat marchand et secrets injectés côté serveur.

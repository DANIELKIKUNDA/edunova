# LOT 11 — Certification machine v0.12.0

## Backend
```bash
cd services/api
python -m compileall -q app
pytest -q
```

## Back-office Web
```bash
cd apps/admin
flutter pub get
flutter analyze
flutter test
flutter build web --release --dart-define=EDUNOVA_API_URL=https://api.example.com
```

## UX à certifier
- 390×844 : navigation basse, aucune coupure ;
- 768×1024 : navigation adaptée ;
- 1440×900 : NavigationRail et densité desktop ;
- thème sombre ;
- texte 200 % ;
- login invalide ;
- accès sans rôle éditorial = refus explicite ;
- file de revue vide/non vide ;
- publication et retour visible dans le catalogue étudiant.

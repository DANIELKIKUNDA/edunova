# LOT 10 — Certification machine v0.11.1

## 1. Génération et analyse
```bash
cd apps/mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
```

## 2. Formats visuels obligatoires
Tester au minimum :
- Android 360×800 ;
- Android 412×915 ;
- iPhone/PWA 390×844 ;
- tablette 800×1280 ;
- Windows/Web 1366×768 ;
- Windows/Web 1920×1080.

## 3. Accessibilité
- taille de texte 100 %, 150 %, 200 % ;
- thème clair et sombre ;
- réduction des animations ;
- lecture TalkBack/VoiceOver des KPI et du graphique ;
- navigation clavier sur Windows/Web.

## 4. Scénarios UX
- première semaine avec données limitées ;
- forte progression ;
- rythme stable ;
- baisse d'activité sans langage culpabilisant ;
- 0 recommandation ;
- 5 recommandations ;
- 0 cours ;
- plus de 6 cours ;
- cours sans readiness ;
- cours avec échéance dans 1 jour ;
- activité de 14 jours incluant jours vides ;
- refresh pull-to-refresh ;
- erreur repository ;
- drill-down cours ;
- deep-link vers quiz/flashcards/cours/planning.

## 5. Builds
```bash
flutter build apk --release
flutter build web --release
flutter build windows --release
# iOS via CI macOS plus tard
```

## Statut
OPEN-machine tant que ces étapes n'ont pas été exécutées sur SDK Flutter réel.

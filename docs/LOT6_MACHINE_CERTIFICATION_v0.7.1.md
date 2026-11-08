# LOT 6 v0.7.1 — Certification machine

## Backend
```bash
cd services/api
pip install -r requirements.txt
python -m compileall -q app tests
pytest -q
```
Attendu : **155 tests PASS**.

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

Scénarios supplémentaires v0.7.1 :
1. migration Drift v9 -> v10 ;
2. un follow-up « explique la deuxième étape » reçoit les 6 derniers tours, jamais plus ;
3. changement Essentiel -> Approfondi ne réutilise pas un cache incompatible ;
4. grounding/source count restent disponibles après fermeture/réouverture ;
5. un document avec instruction malveillante n'envoie pas cette instruction au modèle ;
6. réponse rejetée pour grounding insuffisant affiche 0 crédit ;
7. citations restent ouvrables après réponse issue du fallback ;
8. historique personnel reste local après déconnexion/reconnexion.

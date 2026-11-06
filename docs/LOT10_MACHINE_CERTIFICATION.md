# LOT 10 — Certification machine

Exécuter après extraction du checkpoint :

```powershell
cd apps/mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter build apk --debug
flutter build web
flutter build windows
```

## Scénarios UX obligatoires
1. base neuve sans activité : preuve limitée, pas de faux verdict ;
2. 7 jours d'activité : cartes comparatives correctes ;
3. interrogation dans 48 h + readiness faible : recommandation prioritaire ;
4. cours sans quiz : readiness calculé avec les signaux existants ;
5. recommandation « Plus tard » : disparaît 24 h puis revient ;
6. recommandation masquée : reste absente ;
7. textes à 200 % : aucune troncature critique ;
8. mode sombre : contrastes lisibles ;
9. largeur 360 px, tablette, desktop : grille adaptative ;
10. migration Drift v15→v16 préserve toutes les données LOT 1–9.

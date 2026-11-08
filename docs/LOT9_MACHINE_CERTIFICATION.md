# LOT 9 — Certification machine

## Flutter
```bash
cd apps/mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter build apk --debug
flutter build web
flutter build windows
```

## Scénarios notifications
1. refuser puis accepter la permission ;
2. programmer J-3/J-1/H-3 ;
3. vérifier le maximum quotidien ;
4. vérifier les heures calmes ;
5. tuer/reouvrir l’app et confirmer que les rappels sont toujours présents ;
6. modifier une date d’examen et confirmer la reprogrammation ;
7. vérifier les deep-links depuis notification ;
8. vérifier Android et iOS séparément.

## Scénarios audio
1. ouvrir un résumé Premium ;
2. tester 0,75×/1×/1,25×/1,5×/2× ;
3. pause/reprise ;
4. fermer/reouvrir et reprendre la position ;
5. ajouter puis réouvrir un repère ;
6. vérifier un texte contenant %, °C, →, Δ, µ ;
7. compte gratuit : vérifier l’aperçu limité ;
8. écran verrouillé / écoute prolongée à certifier sur Android/iOS.

## Push distant
En staging seulement, configurer les credentials Firebase et `FCM_ENABLED=true`. Vérifier envoi, deep-link et révocation des jetons invalides.

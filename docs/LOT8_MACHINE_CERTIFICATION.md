# LOT 8 — Certification machine

## Flutter
```powershell
cd apps/mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter build apk --debug
flutter build windows --debug
flutter build web
```

## Scénario réseau réel
1. Télécharger une ressource >= 20 Mo.
2. Couper Internet à ~30 %.
3. Fermer EduNova.
4. Rouvrir et rétablir Internet.
5. Vérifier reprise depuis `bytesDownloaded`, pas depuis zéro.
6. Vérifier SHA-256 final.

## PWA
- Installer la PWA.
- Télécharger une ressource autorisée offline.
- Fermer complètement le navigateur.
- Rouvrir hors ligne.
- Vérifier persistance des chunks et état `ready`.

## R2/S3 staging
Variables : `CONTENT_STORAGE_BUCKET`, `CONTENT_STORAGE_ENDPOINT`, `CONTENT_STORAGE_REGION`, `RESOURCE_DELIVERY_SECRET`.
- Uploader un objet avec metadata `sha256`.
- Enregistrer le même checksum dans `library_resources`.
- Vérifier grant direct.
- Modifier volontairement le metadata SHA-256 et confirmer blocage `delivery_storage_checksum_mismatch`.

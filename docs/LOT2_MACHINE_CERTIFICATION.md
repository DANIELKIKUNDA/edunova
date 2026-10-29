# LOT 2 — Certification machine Flutter

Cette checklist doit être exécutée avant de fermer LOT 2.

## 1. Préparer Flutter

```powershell
cd apps/mobile
flutter doctor -v
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
```

## 2. Android

- importer un PDF texte de 100+ pages ;
- vérifier ouverture in-app ;
- vérifier zoom/recherche/navigation ;
- importer une photo d'interrogation ;
- vérifier stockage privé ;
- tester fermeture/réouverture et reprise ;
- couper Internet et répéter ;
- confirmer qu'aucun fichier privé n'est envoyé au backend en mode `deviceOnly`.

## 3. iOS

Même grille que Android, avec validation caméra, stockage privé et notifications locales.

## 4. Windows

- import PDF/image ;
- lecteur ;
- OCR local ;
- reprise ;
- hors connexion.

## 5. PWA

- OPFS ;
- persistance après fermeture du navigateur ;
- comportement lorsque l'utilisateur efface les données du site ;
- lecture offline ;
- extraction/OCR local WebAssembly ou consentement explicite `onlineAssist`.

## 6. Gates de fermeture

LOT 2 est CLOSED seulement lorsque :

- Drift v2 généré sans erreur ;
- `flutter analyze` = 0 erreur ;
- `flutter test` = PASS ;
- Android réel = PASS ;
- au moins une cible iPhone/PWA = PASS ;
- confidentialité device-only = PASS ;
- PDF texte + PDF scanné + photo interrogation = PASS.

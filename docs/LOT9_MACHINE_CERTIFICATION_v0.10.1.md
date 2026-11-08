# LOT 9 v0.10.1 — Certification machine UX/UI

## A. Build & statique
- `flutter pub get`
- `dart run build_runner build --delete-conflicting-outputs`
- `flutter analyze` : 0 erreur
- `flutter test` : tous PASS, y compris `test/ux/premium_surface_test.dart`

## B. Matrice responsive
Tester au minimum :
- Android 360×800 et 412×915
- iPhone/PWA 390×844 et 430×932
- tablette 800×1280
- Windows/Web 1024×768, 1366×768 et 1920×1080

Attendus :
- bottom navigation sous 920 px ; NavigationRail au-dessus ;
- aucun overflow à text scale 100 %, 150 % et 200 % ;
- largeur de lecture bornée et contenus centrés sur écran large.

## C. Thèmes & accessibilité
- clair + sombre ;
- text scale 2× ;
- lecteur d'écran : boutons icon-only nommés ;
- mode réduction d'animations : transitions non essentielles réduites ;
- contraste de tous les états Premium/erreur/succès contrôlé visuellement.

## D. Notifications Android/iOS
- permission jamais demandée au premier lancement sans action utilisateur ;
- sheet explicative puis prompt système ;
- toucher un rappel en premier plan/arrière-plan ouvre le deep-link ;
- lancer l'app depuis notification fermée ouvre le deep-link ;
- historique récent visible ;
- heures calmes et plafond respectés.

## E. PWA/Windows
- bouton permission locale native non affiché comme disponible lorsqu'il ne l'est pas ;
- le texte explique le canal distant ;
- aucun blocage de l'application si FCM/Web Push n'est pas configuré.

## F. Audio
- play/pause/reprise ;
- seek via slider ;
- vitesse 0,75× / 1× / 1,25× / 1,5× / 2× ;
- changement de vitesse pendant lecture reprend au bon offset ;
- repères ;
- transcript ;
- aperçu gratuit limité ;
- Premium complet ;
- interruption appel/audio système puis reprise à vérifier ;
- écran verrouillé à tester séparément.

## G. Acceptation visuelle
Capturer au minimum :
1. Accueil clair mobile
2. Accueil sombre mobile
3. Accueil desktop NavigationRail
4. Rythme
5. Rappels + historique
6. Réglages notifications
7. Permission rationale sheet
8. Audio Premium
9. Audio gratuit
10. Empty state / Error state

Le lot UX ne peut être déclaré CLOSED que lorsque ces captures sont revues sans overflow, incohérence d'espacement ou donnée factice.

# LOT 9 — Critères d’acceptation

## Backend
- [x] préférences de notification versionnées côté compte ;
- [x] fuseau/offset, heures calmes et plafond quotidien ;
- [x] déduplication ;
- [x] remplacement par priorité ;
- [x] agrégats d’activité idempotents/monotones ;
- [x] calcul streak ;
- [x] registre d’appareils push ;
- [x] FCM optionnel et désactivé sans configuration ;
- [x] worker de dispatch ;
- [x] migration `0006_engagement_notifications_v0_10_0.sql` ;
- [x] 210 tests backend PASS.

## Flutter/code préparé
- [x] Drift v15 ;
- [x] préférences engagement locales ;
- [x] historique d’activité local ;
- [x] notification intents enrichis ;
- [x] filtre anti-spam local ;
- [x] permission notification déclenchée depuis l’UI ;
- [x] TTS local ;
- [x] reprise de lecture et repères ;
- [x] audio complet Premium / aperçu gratuit ;
- [x] accès audio depuis un cours ;
- [x] écran rythme & notifications ;
- [x] intégration accueil/profil.

## OPEN-machine
- [ ] `flutter pub get` avec plugins notifications/TTS ;
- [ ] génération Drift v15 ;
- [ ] `flutter analyze` ;
- [ ] `flutter test` ;
- [ ] permission Android 13+ réelle ;
- [ ] permission iOS réelle ;
- [ ] rappel après kill/reboot appareil ;
- [ ] TTS verrouillage écran ;
- [ ] PWA Web Push avec vraie configuration ;
- [ ] FCM staging avec jeton réel.

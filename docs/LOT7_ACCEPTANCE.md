# LOT 7 — Matrice d'acceptation

## Certifié dans l'environnement ChatGPT
- [x] backend historique sans régression ;
- [x] push idempotent ;
- [x] rejeu d'un conflit reproduit le conflit canonique ;
- [x] conflit de version explicite ;
- [x] progression monotone multi-appareils ;
- [x] append-only immuable ;
- [x] données local-only rejetées ;
- [x] données financières génériques non poussables ;
- [x] isolation entre comptes ;
- [x] snapshot bootstrap ;
- [x] pull incrémental ;
- [x] catalogue publié uniquement ;
- [x] catalogue freemium consultable sans authentification ;
- [x] ressource Premium verrouillée ;
- [x] aucune fuite de `storage_locator` ;
- [x] jeton de livraison lié au compte/ressource/expiration ;
- [x] migration PostgreSQL 0004 couverte par le contrat des migrations.

## À certifier sur machine Flutter
- [ ] `dart run build_runner build --delete-conflicting-outputs` ;
- [ ] migration Drift v10→v11 ;
- [ ] `flutter analyze` ;
- [ ] `flutter test` incluant `cloud_sync_use_case_test.dart` ;
- [ ] build Android ;
- [ ] build Web/PWA ;
- [ ] build Windows ;
- [ ] test réel de deux appareils sur le même compte ;
- [ ] test offline 30 minutes puis reconnexion ;
- [ ] résolution manuelle d'un conflit ;
- [ ] vérification qu'aucun PDF/photo personnel n'apparaît côté serveur.

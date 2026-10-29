# Phase 18 — v0.53.16 — Interfaces commerciales

## Développement effectif
- Écran Flutter central Volcano Tech `PlatformCampusOffersPage`: consultation, création, modification, publication/dépublication, validation locale, versionnement optimiste, erreurs 403/409 et rechargement.
- Route `/platform/campus-offers` enregistrée. Les opérations restent contrôlées par `platform.roles.manage` côté backend.
- Paiement Campus Flutter: choix explicite de l'offre payante, montant, capacité et durée visibles, sans sélection silencieuse de la première offre; statut vérifié côté serveur.
- Services de commande, confirmation fournisseur signée, activation transactionnelle et idempotence déjà présents dans v0.53.15 et préservés.

## Vérifications
- `PYTHONPATH=services/api python -m pytest -q services/api/tests/test_phase18* services/api/tests/test_migration_contract.py`: **84 passed**.
- Régression générale tentée mais interrompue au timeout; pas de résultat PASS global.
- Flutter SDK indisponible: aucun `flutter analyze`, `flutter test`, `flutter build` exécuté.
- Agrégateur de production, clés, callbacks externes et essais réels restent à intégrer/certifier sur l'environnement utilisateur.

## État de clôture
Le développement des trois parcours commerciaux principaux est présent côté backend et Flutter. **La Phase 18 est livrable pour passage à la Phase 19 en statut 'développement local réalisé, certification Flutter/production réservée'**, pas certifiée intégralement. La Phase 19 (consolidation mobile/offline/UX) et la Phase 23 (appareils réels) figurent dans la feuille de route existante; les phases intermédiaires doivent être relues avant de promettre un nombre définitif.

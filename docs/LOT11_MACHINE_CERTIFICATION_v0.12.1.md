# Certification machine — LOT 11 v0.12.1

## Pré-requis
Flutter stable récent + Chrome/Edge.

## Commandes
```bash
cd apps/admin
flutter pub get
flutter analyze
flutter test
flutter build web --release
```

## Scénarios obligatoires
1. login valide + restauration de session après refresh navigateur ;
2. compte sans rôle éditorial refusé ;
3. responsive 390×844, 768×1024, 1024×768, 1440×900 ;
4. thème clair/sombre ;
5. création → révision → relecture → publication ;
6. checklist médicale ;
7. validation OCR par une autre personne ;
8. conflit optimiste avec deux onglets ouverts ;
9. affectation + échéance ;
10. archivage : disparition du catalogue public ;
11. clavier seul + focus visible ;
12. zoom navigateur 200 % sans overflow bloquant.

LOT 11 ne passe à CLOSED qu'après ces scénarios.

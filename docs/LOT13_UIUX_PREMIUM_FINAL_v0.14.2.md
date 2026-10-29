# LOT 13 — UI/UX Premium Final v0.14.2

## Objectif
Transformer la vue Content Factory en poste de contrôle éditorial professionnel, dense sur desktop et réellement exploitable sur tablette/mobile, sans modifier le contrat métier stabilisé du LOT 13.

## UX livrée
- cockpit KPI responsive : corpus, production, revue, blocages, qualité moyenne ;
- recherche locale rapide, filtres d'état et tris qualité/risque ;
- master-detail desktop pour éviter les allers-retours ;
- bottom sheet de revue sur écrans compacts ;
- dossier de revue en trois vues : Artefacts, Qualité, Traçabilité ;
- comparaison artefact ↔ preuve source avec pages et extrait sélectionnable ;
- filtres par type d'artefact ;
- score de confiance et score qualité visibles sans ouvrir le détail ;
- états loading / empty / no-result / offline-error dédiés ;
- libellés métier en français au lieu des états techniques bruts ;
- Semantics sur les cartes de run et hiérarchie visuelle accessible ;
- rappel permanent : aucune publication automatique, validation humaine obligatoire ;
- densité responsive 2/3/5 KPI selon largeur ;
- refresh manuel et pull-to-refresh.

## Non-régression métier
Aucun changement de gouvernance : `READY_FOR_REVIEW` reste la sortie maximale de Content Factory. La publication reste hors de ce module et sous gouvernance Studio.

## OPEN-machine
Flutter SDK n'étant pas disponible dans l'environnement ChatGPT : `flutter pub get`, `flutter analyze`, `flutter test`, builds Web/Windows/Android et revue visuelle sur navigateurs/appareils réels restent à certifier sur machine.

# EduNova v0.53.2 — Phase 18, droits commerciaux dans Flutter

## Réalisé
- `CommerceRemoteGateway.getCombinedAccess` expose l'API authentifiée `GET /v1/commerce/combined-access` avec identifiant institutionnel optionnel.
- `combinedAccessProvider` interroge le serveur pour le compte authentifié.
- Écran Premium : carte « Mes accès EduNova », état de chargement, panne réseau et séparation explicite des droits personnels/Campus.
- Après paiement confirmé, invalidation du cache des droits combinés.
- Tests de contrat Flutter/API ajoutés.

## Limites explicites
- L'écran Premium ne connaît pas l'université sélectionnée : il vérifie les droits personnels uniquement et ne présente **pas** un faux état Campus négatif. La vérification Campus exige de passer l'identifiant institutionnel depuis l'espace Campus, à raccorder dans le lot suivant.
- SDK Flutter absent de cet environnement : compilation et tests Flutter non exécutés.
- Le contrôle d'autorisation serveur reste la source de vérité; cet affichage ne donne aucun droit supplémentaire.
- La Phase 18 reste ouverte.

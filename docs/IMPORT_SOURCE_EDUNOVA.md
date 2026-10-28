# EduNova — préparation de l'import du code source

Ce dépôt est en cours de préparation pour recevoir le code source officiel EduNova de Volcano Tech.

## Source de référence à contrôler
- Archive candidate : `EduNova_PHASE19_LIVRAISON_FINALE_A_CERTIFIER.zip`
- Cette archive est une **livraison à certifier**, pas une version de production certifiée.
- Périmètre attendu : backend, applications Flutter mobile/admin, tests, migrations, ressources et documentation.
- Vérifier l'intégrité, les versions et les secrets avant import.

## Sécurité
Le dépôt étant actuellement public, **ne pas y publier** de secrets, données réelles d'étudiants, identifiants, clés de paiement, fichiers de configuration sensibles ou exports de bases de données. Un `.gitignore` ne remplace pas l'audit de contenu.

## Procédure de transfert
1. Examiner la structure et le contenu de l'archive candidate.
2. Identifier et retirer les éléments sensibles et générés.
3. Importer le code source sur une branche dédiée, sans écraser `main`.
4. Exécuter les vérifications backend, Flutter et les tests disponibles.
5. Faire une revue des changements, puis fusionner après validation.

Statut : **préparation uniquement ; import complet non effectué**.

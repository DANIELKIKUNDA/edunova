# EduNova — Phase 19, point A — audit des accès locaux (v0.56.0)

## Modifications effectives
- `BootstrapPage` vérifie la session et la propriété des données **avant** de charger `academicProfileProvider` et de déclencher les tâches de téléchargement, d'engagement et de notifications.
- En l'absence de session, une installation possédant un propriétaire persistant ou des données historiques non attribuées est redirigée vers `/login`, sans ouvrir le profil.
- Une installation neuve et vide conserve l'accès au parcours d'accueil hors connexion.
- `LoginPage` sait maintenant revenir au bootstrap lorsqu'elle est ouverte comme route racine (et non seulement comme écran empilé).

## Vérifications
- Backend sync : `17 passed in 15.90s`.
- SDK Flutter/Dart absent : compilation, analyse statique et tests Flutter non exécutés.
- Archive complète : test d'intégrité ZIP effectué.

## Risques encore ouverts — ne pas déclarer la certification maximale
1. Le routeur `GoRouter` ne dispose pas d'un garde global pour **toutes** les routes profondes : un lien direct vers un écran métier peut contourner le bootstrap. Cette protection doit être traitée avant clôture du point A.
2. La politique « propriétaire unique par installation » ne partitionne pas physiquement SQLite. Elle doit rester explicitement documentée.
3. Les installations historiques orphelines sont bloquées mais n'ont pas de procédure de récupération authentifiée.
4. La validation Flutter et sur appareil n'est pas disponible ici ; l'essai sur appareils réels appartient à la Phase 23.

## Décision
Point A : progression réelle, **non clôturé** tant que la navigation profonde n'est pas protégée. Ne pas passer au point B pour l'instant.

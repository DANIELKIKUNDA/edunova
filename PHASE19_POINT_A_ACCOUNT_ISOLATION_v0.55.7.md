# EduNova v0.55.7 — Phase 19, point A

## Correctifs réalisés
- `SecureSessionStore.read()` rattache immédiatement au compte authentifié toute ancienne session valide qui ne possède pas encore `auth.localDataOwner`. Cela empêche qu'une déconnexion ultérieure permette la réattribution silencieuse de l'installation.
- `NativeOfflineResourceStore._dir()` rejette les identifiants de ressources contenant des séparateurs de chemin, points ou autres caractères non autorisés. Cela évite qu'un identifiant distant malformé provoque des opérations de fichiers hors du cache attendu.
- Nouveau test Flutter de migration de propriété lors de la lecture d'une session ancienne.

## Vérifications
- Backend sync : 17 tests réussis.
- Flutter SDK absent : tests Flutter et analyse statique non exécutés.
- Les téléchargements restent dans un cache global de l'installation : la stratégie actuelle est **un seul propriétaire par installation**, et non un véritable multi-compte.

## Risques encore ouverts — point A non certifié
- Anciennes installations possédant des données SQLite mais aucun compte authentifié ni marqueur propriétaire : impossible de déduire le propriétaire sans procédure de migration/quarantaine contrôlée.
- Les écrans métier ne contrôlent pas tous directement le propriétaire avant de lire la base ; l'application doit garantir ce contrôle à l'entrée de session.
- La séparation des fichiers de cache par compte n'est pas implémentée ; elle repose sur l'exclusivité de l'installation.
- Tests Flutter à exécuter dans une machine avec SDK et scénarios de migration réelle à valider.

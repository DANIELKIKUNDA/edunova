# EduNova v0.55.8 — Phase 19 / Point A : données historiques sans propriétaire

## Modifications réelles
- `SecureSessionStore.ownerAccountId()` : lecture sérialisée de l'identité persistante du propriétaire.
- `ApiIdentityRepository._assertLocalAccountOwnership()` : vérification du propriétaire, rejet d'un propriétaire différent, et, en l'absence de propriétaire, détection de lignes dans les tables SQLite `local_*` avant toute attribution de compte.
- Une ancienne installation avec données locales mais sans propriétaire ni session récupérable échoue désormais avec `unowned_legacy_local_data`, plutôt que de rattacher les données à un nouveau compte.
- Une installation vide peut être attribuée à son premier utilisateur; une installation déjà attribuée conserve son propriétaire après déconnexion.

## Limites et certification
- La protection est une politique **mono-propriétaire par installation**, et non un multi-compte isolé avec données partitionnées.
- La politique de récupération/migration manuelle des données orphelines n'est pas implémentée. Aucun effacement automatique.
- Les fichiers téléchargés et les accès métier doivent être vérifiés dans l'audit transversal; le SDK Flutter est indisponible ici, donc analyse statique et tests Flutter non exécutés.
- Les 17 tests backend de synchronisation ont affiché `17 passed` ; l'enveloppe d'exécution a néanmoins signalé un timeout après cette sortie.
- Point A : **code renforcé, non certifié Flutter**. Ne pas confondre avec clôture finale.

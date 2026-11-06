# LOT 6 — Preuves ChatGPT

Date : 2026-09-21

## Batterie backend
Commande :
```bash
cd services/api
pytest -q
```
Résultat après durcissement multi-fournisseurs, circuit breaker, FTS PostgreSQL et contrat migrations :

**143 passed**

## Compilation Python
```bash
python -m compileall -q services/api/app services/api/tests
```
Résultat : PASS.

## Points spécifiquement testés
- RAG sourcé et abstention ;
- cache commun sans seconde facturation ;
- confidentialité documents personnels ;
- SymPy à coût IA nul ;
- budget global ;
- réservation/restitution crédits ;
- fallback ;
- configuration multi-fournisseurs ;
- circuit breaker ;
- PostgreSQL FTS compilé et borné au cours ;
- migrations couvrant toutes les tables SQLAlchemy exactement une fois.

## Audit statique complémentaire
- `compileall` : PASS ;
- aucun `TODO`, `FIXME` ou `NotImplementedError` dans le cœur ;
- aucun corps de fonction réduit à `pass` ;
- Drift `schemaVersion = 9` ;
- 293 fichiers utiles avant nettoyage/package.

## Limite honnête
Flutter/Dart n'est pas disponible dans l'environnement ChatGPT courant. Aucune certification Flutter n'est revendiquée ici.

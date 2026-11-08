# LOT 6 — Certification machine

## Backend local / CI
```bash
cd services/api
pip install -r requirements.txt
python -m compileall -q app tests
pytest -q
```
Attendu pour le checkpoint ChatGPT : **143 tests PASS**.

## PostgreSQL
Appliquer dans l'ordre :
1. `0001_identity_commerce.sql`
2. `0002_commerce_hardening_v0_6_1.sql`
3. `0003_assistant_rag_v0_7_0.sql`

Vérifier ensuite que l'index `ix_knowledge_chunks_fts_fr` existe.

## Redis
En environnement de recette :
- définir `AI_DAILY_CREDIT_BUDGET` à une petite valeur ;
- vérifier qu'un appel réussi réserve puis commit ;
- vérifier qu'un échec provider libère la réservation ;
- vérifier que plusieurs workers partagent le même plafond.

## Flutter
```bash
cd apps/mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter build apk --debug
flutter build web
flutter build windows --debug
```

Scénarios obligatoires :
1. migration Drift v8 -> v9 ;
2. conversation sauvegardée après fermeture/réouverture ;
3. citation personnelle ouvre la bonne page ;
4. document personnel refuse l'envoi sans consentement ;
5. mode avion conserve l'historique mais ne prétend pas appeler l'IA ;
6. quota épuisé affiche une erreur compréhensible ;
7. plafond global atteint n'enlève aucun crédit utilisateur ;
8. réponse cache affiche 0 crédit ;
9. messages avec flags de sécurité restent lisibles ;
10. Android/Web/Windows restent cohérents visuellement.

## Production
Ne jamais activer l'IA externe avec :
- un fournisseur non benchmarké ;
- des clés dans le dépôt ;
- `AI_DAILY_CREDIT_BUDGET=0` en pensant que 0 signifie illimité : ici **0 bloque** ;
- documents personnels autorisés sans décision explicite de confidentialité.

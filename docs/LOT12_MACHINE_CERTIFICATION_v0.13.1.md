# LOT 12 — certification machine

## Backend / Docker
```bash
docker compose up -d postgres redis
# environnement production-security pour ClamAV lors d'un test proche production
docker compose --profile production-security up -d clamav
cd services/api
pytest -q
python -m compileall -q app
```

## Worker
```bash
python -m app.modules.ingestion.worker
```
Tester interruption forcée du worker pendant OCR, attendre expiration du lease, puis vérifier la reprise.

## Flutter Studio
```bash
cd apps/admin
flutter pub get
flutter analyze
flutter test
flutter build web --release
```

## Scénarios E2E obligatoires
1. lot de 200 PDF/scans ;
2. 2 workers simultanés sans double traitement ;
3. coupure d'un worker ;
4. faux PDF / PDF chiffré / image géante ;
5. fichier EICAR dans environnement isolé ;
6. bundle 10 photos ;
7. doublon même contexte ;
8. doublon contexte/droits différents ;
9. dead-letter + retry manuel ;
10. brouillon Studio + vérification OCR + publication LOT 11.

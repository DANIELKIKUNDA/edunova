# LOT 7 — Certification machine

1. Décompresser le checkpoint dans un nouveau dossier.
2. Backend : appliquer les migrations 0001→0004 puis exécuter `pytest -q`.
3. Mobile : `flutter pub get` puis `dart run build_runner build --delete-conflicting-outputs`.
4. Exécuter `flutter analyze` et `flutter test`.
5. Installer deux clients (ex. Android + PWA) avec le même compte.
6. Hors ligne sur A : modifier horaire/échéance/préférences. Synchroniser A puis B et vérifier la convergence.
7. Modifier la même préférence différemment hors ligne sur A et B. Vérifier qu'un conflit apparaît et qu'aucune version n'est écrasée silencieusement.
8. Importer un PDF personnel puis inspecter le serveur : aucun binaire, OCR ou chunk personnel ne doit être créé par Sync.
9. Charger le catalogue EduNova sans compte et vérifier les ressources Premium verrouillées.
10. Vérifier le checksum d'une ressource offline lorsque l'adaptateur R2/S3 réel sera branché.

LOT 7 reste `OPEN-machine` tant que ces étapes Flutter/multi-appareils ne sont pas réalisées.

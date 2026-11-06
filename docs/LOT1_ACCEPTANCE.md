# LOT 1 — Critères d’acceptation

## Scénarios à certifier sur la machine Flutter

1. Premier lancement sans profil -> onboarding.
2. Faculté, programme, niveau et semestre sont obligatoires ; université facultative.
3. Après validation, relance de l’application -> accès direct à l’accueil.
4. `Mes cours > Mes documents > Ajouter` accepte PDF/JPG/JPEG/PNG/WEBP.
5. La caméra permet de photographier une ancienne interrogation sur Android/iOS.
6. Le fichier natif est copié sous l’espace privé de l’application.
7. Le document apparaît dans la bibliothèque après import.
8. Le type (cours/interrogation/examen/exercice/notes/autre) est conservé.
9. Aucun upload HTTP n’est déclenché par l’import local.
10. Un événement de métadonnées est créé dans l’outbox locale.
11. L’application reste exploitable hors connexion pour les données locales déjà enregistrées.
12. Dark mode / light mode restent cohérents.

## Commandes de certification

```powershell
./scripts/bootstrap_flutter.ps1
```

Le script génère les cibles Flutter, récupère les dépendances, génère Drift, exécute `flutter analyze` et `flutter test`.

Backend :

```bash
cd services/api
pytest -q
```

## Limites connues volontairement ouvertes

- Stockage binaire PWA/OPFS : lot Web/offline.
- OCR réel : lot OCR.
- Chiffrement au repos final : lot sécurité.
- Sync backend : lot synchronisation.
- Lecteur PDF enrichi : lot contenu.

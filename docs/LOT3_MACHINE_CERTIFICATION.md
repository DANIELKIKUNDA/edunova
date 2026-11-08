# LOT 3 — Certification machine

## Windows / Android / Web

```powershell
cd apps/mobile
flutter doctor -v
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter build windows --debug
flutter build apk --debug
flutter build web --release
```

## Scénario fonctionnel minimum

1. Ouvrir EduNova et terminer l’onboarding.
2. Ouvrir `Mes cours > Physiologie générale`.
3. Vérifier les quatre onglets : Résumé, Flashcards, Quiz, Mes erreurs.
4. Injecter/charger un jeu de données de test.
5. Réviser une carte et redémarrer : l’échéance doit être conservée.
6. Répondre faux à une question : elle apparaît dans Mes erreurs.
7. Répondre juste deux fois sur cette même notion : l’erreur doit être marquée récupérée.
8. Terminer un quiz et vérifier la ligne `LocalQuizAttempts` et ses `LocalQuizAnswers`.
9. Passer hors ligne et répéter une session déjà téléchargée.

Joindre les sorties console et captures au dossier `docs/evidence/lot3/`.

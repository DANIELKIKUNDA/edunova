# Préparation locale réellement effectuée

Ces commandes complètent l’inventaire instrumenté de COMMANDS.md. Les chemins
sont ceux de cette machine Windows. Les reprises réseau ont été exécutées après
autorisation hors sandbox ; aucun secret d’environnement n’est imprimé.

```text
git clone --branch import/edunova-v0.57.12 --single-branch https://github.com/DANIELKIKUNDA/edunova.git edunova
git status --short --branch
git rev-parse HEAD
git remote -v
where git
where python
where flutter
where dart
where psql
where docker
git --version
psql --version
docker version
..\.venv\Scripts\python.exe --version
..\.venv\Scripts\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r services\api\requirements.txt
.venv\Scripts\python.exe -m pip install pytest-xdist==3.8.0
.venv\Scripts\python.exe -m pytest -q -x services/api/tests/assistant
.venv\Scripts\python.exe -m pytest -q -x services/api/tests/content_factory/test_content_factory.py
C:\Users\cs-ap\dev\flutter\bin\flutter.bat --version
C:\Users\cs-ap\dev\flutter\bin\flutter.bat doctor -v
C:\PROGRA~1\PostgreSQL\16\bin\initdb.exe -D .local-certification\postgres -U edunova_cert --auth=trust --encoding=UTF8 --locale=C
C:\PROGRA~1\PostgreSQL\16\bin\pg_ctl.exe -D .local-certification\postgres -l .local-certification\postgres-server.log -w start
C:\PROGRA~1\PostgreSQL\16\bin\createdb.exe -h 127.0.0.1 -p 55439 -U edunova_cert edunova_phase19_test
```

Le serveur reçoit une configuration dédiée : `listen_addresses='127.0.0.1'`,
`port=55439`, `max_connections=40`, `shared_buffers='32MB'`. Elle est incluse depuis
`.local-certification/server.conf`. Les migrations sont ensuite exécutées par
`scripts/certify_phase19_migrations.py`, avec arrêt sur la première erreur.

Les hôtes Flutter manquants ont été générés dans chaque application par
`flutter create --platforms=web,windows --no-pub .`, puis
`flutter create --platforms=android --no-pub .`. Les tests compteur de démonstration
créés par cet outil ont été retirés ; les tests EduNova existants sont conservés.

Tesseract a été téléchargé depuis la release 5.5.3 liée par la documentation
UB Mannheim, puis installé silencieusement dans `.local-certification/tesseract`.
Le modèle français provient de `tesseract-ocr/tessdata_fast/main/fra.traineddata`.
NuGet provient de `https://dist.nuget.org/win-x86-commandline/v6.14.0/nuget.exe`.
Les fichiers binaires de préparation restent hors Git dans `.local-certification`.

Les builds Android ont installé leurs prérequis manquants : plateforme Android 35,
NDK 27.0.12077973 et CMake 3.22.1. Le réglage Java 17 et
`com.android.tools:desugar_jdk_libs:2.1.4` suit le README de
flutter_local_notifications 20.1.0 réellement résolu.

Le téléchargement PDFium Android x86_64 a été diagnostiqué séparément via curl,
avec le même tag `chromium%2F7202` et la même URL que pdfrx 1.3.5. Ce diagnostic
n’a pas modifié le plugin ni injecté une bibliothèque dans son cache. Le build
Flutter complet a finalement terminé son propre assemblage.

Le composant Visual Studio `Microsoft.VisualStudio.Component.VC.ATL` a été ajouté
par `Installer/setup.exe modify --installPath <Visual Studio Community 2022>
--add Microsoft.VisualStudio.Component.VC.ATL --quiet --norestart`, avec élévation
Windows. Sa sortie et sa vérification sont conservées dans les fichiers `atl-*`.

Avant correction, le cache CMake mobile contenait exactement
`CMAKE_INSTALL_PREFIX:PATH=C:/Program Files/edunova`. Cette valeur venait de la
configuration interrompue avant la section d’installation Flutter. La récupération
du préfixe bundle a été ajoutée aux CMakeLists.txt ; le build a été rejoué.

Le cluster dédié est arrêté après les tests : voir `postgres-stop.log`. Les données
restent présentes pour une reprise locale ; aucune base existante n’a été modifiée.

Les deux reproductions pytest ci-dessus ont respectivement donné 38 réussites
(`backend-first-failure.log`) et un premier échec OCR avant correction
(`content-factory-first-failure.log`). Elles ne s’ajoutent pas aux nombres uniques
de la régression finale.

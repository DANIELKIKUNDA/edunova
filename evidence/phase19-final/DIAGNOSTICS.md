# Tentatives non réussies et corrections

Les codes non nuls restent conservés, même après une reprise réussie. Les JSON associés contiennent la commande, le commit et le répertoire exacts.

- FastAPI 0.162 utilise des routeurs inclus effectifs : trois tests inspectaient seulement la liste de premier niveau. Adaptation à `iter_route_contexts`, sans suppression des assertions d’unicité, de méthode ni de dépendance `current_auth` ; ajout de requêtes internes sans authentification exigeant 401.
- Le nouveau test workspace a révélé un débordement de 22 px : titres de rangées non contraints. Correction avec Expanded ; assertion d’absence d’exception conservée.
- Le premier double Admin tentait de surcharger des méthodes d’extension Dart : deux avertissements de surcharge inexistante. Le test intercepte désormais les vraies requêtes HTTP via MockClient, sans modifier l’API de production.
- Dépréciation Drift web : information résiduelle ; les analyses Mobile de code 1 ne sont pas des PASS.
- Premier audit pip : 100 entrées signalées dans cinq paquets. Mises à jour testées séparément ; les résultats avant correction restent disponibles.

## admin-analyze-previous-1793563357244268100

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub`.
Code : 1. Commit : `9dcb12fa7cb4b16a8b3d6ae13b534a20fd35ae44`.
Trace : [admin-analyze-previous-1793563357244268100.log](admin-analyze-previous-1793563357244268100.log).

## backend-final-previous-1793563537890725600

Commande : `C:\Users\cs-ap\dev\edusync-web\edunova\.local-certification\security-venv\Scripts\python.exe -m pytest -q -n 2 --dist loadfile --durations=20 services/api/tests --junitxml=C:\Users\cs-ap\dev\edusync-web\edunova\evidence\phase19-final\backend-final.xml`.
Code : 1. Commit : `edb7876cb26c131ec13c15e33f40b98022801e33`.
Trace : [backend-final-previous-1793563537890725600.log](backend-final-previous-1793563537890725600.log).

## mobile-analyze-previous-1793558143381502200

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub`.
Code : 1. Commit : `716a11fcb8c98073e218290bdc020ed98ade5886`.
Trace : [mobile-analyze-previous-1793558143381502200.log](mobile-analyze-previous-1793558143381502200.log).

## mobile-analyze-previous-1793559338375069200

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub`.
Code : 1. Commit : `793627f1bed4e9b135667c57875ade1df79d575e`.
Trace : [mobile-analyze-previous-1793559338375069200.log](mobile-analyze-previous-1793559338375069200.log).

## mobile-analyze-previous-1793563324157516900

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat analyze --no-pub`.
Code : 1. Commit : `9dcb12fa7cb4b16a8b3d6ae13b534a20fd35ae44`.
Trace : [mobile-analyze-previous-1793563324157516900.log](mobile-analyze-previous-1793563324157516900.log).

## mobile-test-previous-1793563368428396700

Commande : `C:\Users\cs-ap\dev\flutter\bin\flutter.bat test --no-pub --concurrency=1 --reporter=expanded`.
Code : 1. Commit : `9dcb12fa7cb4b16a8b3d6ae13b534a20fd35ae44`.
Trace : [mobile-test-previous-1793563368428396700.log](mobile-test-previous-1793563368428396700.log).

### test_pedagogical_frontend_management_routes_are_authenticated

JUnit : [backend-final-previous-1793563537890725600.xml](backend-final-previous-1793563537890725600.xml).

```text
def test_pedagogical_frontend_management_routes_are_authenticated():
>       _assert_routes(TEACHING_GETS, 'GET')

services\api\tests\test_phase14_15_flutter_completion_contract.py:40: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

paths = ('/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/objectives/report', '/v1/pedagogical-intelli...ing_id}/dashboard', '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/gradebook-reconciliation')
method = 'GET'

    def _assert_routes(paths, method):
        for path in paths:
            matches = [r for r in app.routes if getattr(r, 'path', None) == path
                       and method in getattr(r, 'methods', set())]
>           assert len(matches) == 1, (method, path)
E           AssertionError: ('GET', '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/objectives/report')
E           assert 0 == 1
E            +  where 0 = len([])

services\api\tests\test_phase14_15_flutter_completion_contract.py:32: AssertionError
```

### test_institutional_governed_archive_csv_comparison_routes_are_authenticated

JUnit : [backend-final-previous-1793563537890725600.xml](backend-final-previous-1793563537890725600.xml).

```text
def test_institutional_governed_archive_csv_comparison_routes_are_authenticated():
>       _assert_routes(INSTITUTIONAL_GETS, 'GET')

services\api\tests\test_phase14_15_flutter_completion_contract.py:45: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

paths = ('/v1/institutional-analytics/institutions/{iid}/snapshots', '/v1/institutional-analytics/institutions/{iid}/compariso...{iid}/intelligence/executive-readout', '/v1/institutional-analytics/institutions/{iid}/intelligence/period-comparison')
method = 'GET'

    def _assert_routes(paths, method):
        for path in paths:
            matches = [r for r in app.routes if getattr(r, 'path', None) == path
                       and method in getattr(r, 'methods', set())]
>           assert len(matches) == 1, (method, path)
E           AssertionError: ('GET', '/v1/institutional-analytics/institutions/{iid}/snapshots')
E           assert 0 == 1
E            +  where 0 = len([])

services\api\tests\test_phase14_15_flutter_completion_contract.py:32: AssertionError
```

### test_phase14_15_frontend_paths_are_real_get_endpoints

JUnit : [backend-final-previous-1793563537890725600.xml](backend-final-previous-1793563537890725600.xml).

```text
def test_phase14_15_frontend_paths_are_real_get_endpoints():
        paths = {
            '/v1/campus/me/institutions',
            '/v1/teaching/institutions/{iid}/me/offerings',
            '/v1/campus/institutions/{iid}/periods',
            '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/dashboard',
            '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/gradebook-reconciliation',
            '/v1/institutional-analytics/institutions/{iid}/intelligence/executive-readout',
            '/v1/institutional-analytics/institutions/{iid}/intelligence/period-comparison',
        }
        for path in paths:
            routes = [r for r in app.routes if getattr(r, 'path', None) == path and 'GET' in getattr(r, 'methods', set())]
>           assert len(routes) == 1, path
E           AssertionError: /v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/gradebook-reconciliation
E           assert 0 == 1
E            +  where 0 = len([])

services\api\tests\test_phase14_15_frontend_route_contract.py:17: AssertionError
```

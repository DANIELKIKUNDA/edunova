"""Frontend-BE bridge must target existing authenticated, read-only campus API routes."""
from app.main import app


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
        assert len(routes) == 1, path
        assert any(getattr(dep.call, '__name__', '') == 'current_auth'
                   for dep in routes[0].dependant.dependencies), path


def test_frontend_intelligence_routes_do_not_write_gradebook_or_jury():
    for r in app.routes:
        if not getattr(r, 'path', '').startswith(('/v1/pedagogical-intelligence/institutions/',
                                                 '/v1/institutional-analytics/institutions/')):
            continue
        if getattr(r, 'path', '').endswith(('/dashboard', '/gradebook-reconciliation',
                                           '/intelligence/executive-readout',
                                           '/intelligence/period-comparison')):
            assert getattr(r, 'methods', set()) == {'GET'}

"""Frontend phase 14/15 API bridge: auth and route/method contracts.

Backend assertions do not pretend to compile Flutter; Dart tests are separate.
"""
from app.main import app


TEACHING_GETS = (
    '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/objectives/report',
    '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/dashboard',
    '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/gradebook-reconciliation',
)
TEACHING_MUTATIONS = (
    '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/objectives',
    '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/objectives/{objective_id}/questions',
    '/v1/pedagogical-intelligence/institutions/{iid}/offerings/{offering_id}/assessment-blueprints',
)
INSTITUTIONAL_GETS = (
    '/v1/institutional-analytics/institutions/{iid}/snapshots',
    '/v1/institutional-analytics/institutions/{iid}/comparisons',
    '/v1/institutional-analytics/institutions/{iid}/export.csv',
    '/v1/institutional-analytics/institutions/{iid}/intelligence/executive-readout',
    '/v1/institutional-analytics/institutions/{iid}/intelligence/period-comparison',
)
INSTITUTIONAL_POSTS = ('/v1/institutional-analytics/institutions/{iid}/snapshots',)


def _assert_routes(paths, method):
    for path in paths:
        matches = [r for r in app.routes if getattr(r, 'path', None) == path
                   and method in getattr(r, 'methods', set())]
        assert len(matches) == 1, (method, path)
        route = matches[0]
        assert method in route.methods
        assert any(getattr(dep.call, '__name__', None) == 'current_auth'
                   for dep in route.dependant.dependencies), (method, path)


def test_pedagogical_frontend_management_routes_are_authenticated():
    _assert_routes(TEACHING_GETS, 'GET')
    _assert_routes(TEACHING_MUTATIONS, 'POST')


def test_institutional_governed_archive_csv_comparison_routes_are_authenticated():
    _assert_routes(INSTITUTIONAL_GETS, 'GET')
    _assert_routes(INSTITUTIONAL_POSTS, 'POST')


def test_phase14_15_frontend_never_targets_grade_or_jury_mutation_route():
    paths = (*TEACHING_GETS, *TEACHING_MUTATIONS,
             *INSTITUTIONAL_GETS, *INSTITUTIONAL_POSTS)
    assert all('/gradebook/' not in x and '/jury/' not in x
               and '/students/' not in x and '/published-results/' not in x
               for x in paths)


def test_get_routes_are_not_automatically_exposed_as_mutations():
    for path in (*TEACHING_GETS, *INSTITUTIONAL_GETS):
        matches = [r for r in app.routes if getattr(r, 'path', None) == path]
        assert all('PUT' not in getattr(r, 'methods', set()) and
                   'PATCH' not in getattr(r, 'methods', set()) and
                   'DELETE' not in getattr(r, 'methods', set()) for r in matches)

from app.modules.operations.application.health import OperationalHealthService

def test_liveness_is_process_only():
    x=OperationalHealthService({},version='0.35.0').liveness(); assert x['status']=='alive' and x['version']=='0.35.0'
def test_readiness_passes_when_dependencies_pass():
    ok,p=OperationalHealthService({'db':lambda:None,'redis':lambda:None},version='x').readiness(); assert ok and p['status']=='ready'
def test_readiness_fails_closed_without_leaking_exception():
    def broken(): raise RuntimeError('secret database detail')
    ok,p=OperationalHealthService({'db':broken},version='x').readiness(); assert not ok and p['status']=='not_ready' and p['checks'][0]['detail']=='RuntimeError' and 'secret' not in str(p)

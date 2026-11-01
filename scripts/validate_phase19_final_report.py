"""Validate final report without converting documented reservations into PASS."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
out=root/'evidence/phase19-final'
def data(name): return json.loads((out/name).read_text(encoding='utf-8-sig'))
report=root/'EDUNOVA_PHASE19_CERTIFICATION_FINALE.md'
body=report.read_text(encoding='utf8')
assert '\ufffd' not in body
assert 'PARTIELLEMENT CERTIFIÉ' in body
assert not subprocess.check_output(['git','status','--porcelain','--','apps','services/api'],cwd=root,text=True).strip()
for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',re.sub(r'```.*?```','',body,flags=re.S)):
    if not target.startswith(('https://','http://','#')):
        assert (report.parent/target).exists(), target
required=('audits','backend-final','phase19','postgres','migrations','mobile-pub','admin-pub','mobile-test','admin-test',
          'mobile-web','admin-web','mobile-windows','admin-windows','mobile-android','admin-android','pip-check')
for name in required: assert data(name+'.json')['exit_code']==0, name
audits=data('audits/results.json')
assert len(audits)==55 and all(a['exit_code']==0 for a in audits)
for name in ('backend-final','phase19','postgres'):
    cases=list(ET.parse(out/(name+'.xml')).getroot().iter('testcase'))
    assert cases and not any(c.find('error') is not None or c.find('failure') is not None for c in cases), name
proofs=data('TREE_IDENTITY.json')
for proof in proofs:
    actual=subprocess.check_output(['git','rev-parse','HEAD:'+proof['path']],cwd=root,text=True).strip()
    assert proof['identical'] and actual==proof['tested_tree']==proof['delivered_tree'], proof
artifacts=data('ARTIFACTS.json')
assert len(artifacts)==6
for artifact in artifacts:
    assert artifact['exit_code']==0 and artifact['exists']
    with (root/artifact['path']).open('rb') as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==artifact['sha256']
assert data('admin-analyze.json')['exit_code']==0
mobile=(out/'mobile-analyze.log').read_text(encoding='utf8')
assert not re.search(r'^\s*(error|warning) -',mobile,re.M)
assert 'drift/web.dart' in mobile  # documented residual info; not a clean analysis
result={'report_links':'valid','source_proofs':len(proofs),'verified_builds':len(artifacts),
        'audits_passed':55,'functional_checks':'verified','mobile_analysis':'residual Drift info',
        'verdict':'PARTIELLEMENT CERTIFIÉ'}
(out/'REPORT_VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))

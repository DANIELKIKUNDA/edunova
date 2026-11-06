"""Verify this delivery's recorded evidence, source identities and binary hashes."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
out = root/'evidence/local-phase19'
report = root/'EDUNOVA_CERTIFICATION_LOCALE_PHASE19.md'
body = report.read_text(encoding='utf-8')
source_status = subprocess.check_output(['git','status','--porcelain','--','apps','services/api'],cwd=root,text=True)
assert not source_status.strip(), source_status
assert 'PROVISOIRE' not in body and 'NON TERMINÉ' not in body
assert '\ufffd' not in body and 'CERTIFI\u00c9' in body
for document in (report,out/'COMMANDS.md',out/'FAILURES.md'):
    text = re.sub(r'```.*?```','',document.read_text(encoding='utf-8'),flags=re.S)
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if target.startswith(('http://','https://','#')): continue
        assert (document.parent/target.split('#')[0]).exists(), (document.name,target)
proofs = json.loads((out/'TREE_IDENTITY.json').read_text(encoding='utf-8'))
for item in proofs:
    tested = subprocess.check_output(['git','rev-parse',item['tested_commit']+':'+item['path']],cwd=root,text=True).strip()
    current = subprocess.check_output(['git','rev-parse','HEAD:'+item['path']],cwd=root,text=True).strip()
    assert tested == current == item['tested_tree'] == item['delivery_tree'], item['path']
for name in ('compile','pip-check','migrations','backend-final','backend-contracts','phase19','postgres','mobile-test','admin-test','mobile-web','admin-web','mobile-windows','admin-windows','mobile-android','admin-android'):
    result = json.loads((out/(name+'.json')).read_text(encoding='utf-8'))
    assert result['exit_code']==0, (name,result['exit_code'])
for name in ('mobile-analyze','admin-analyze'):
    log = (out/(name+'.log')).read_text(encoding='utf-8')
    assert not re.search(r'^\s*error -',log,re.M), name
artifacts = json.loads((out/'ARTIFACTS.json').read_text(encoding='utf-8'))
assert len(artifacts)==6
for item in artifacts:
    path = root/item['path']
    assert item['exists'] and path.exists(), item['path']
    with path.open('rb') as handle:
        assert hashlib.file_digest(handle,'sha256').hexdigest()==item['sha256'], item['path']
    if 'abis' in item:
        assert {'arm64-v8a','armeabi-v7a','x86_64'}.issubset(item['abis']), item
for name in ('backend-final','phase19','postgres','backend-contracts'):
    cases = list(ET.parse(out/(name+'.xml')).getroot().iter('testcase'))
    assert not any(case.find('failure') is not None or case.find('error') is not None for case in cases)
result = {'report_links':'valid','utf8':'valid','identical_source_trees':len(proofs),'verified_artifacts':len(artifacts),'functional_failures':0,'verdict':'PARTIELLEMENT CERTIFIÉ'}
(out/'REPORT_VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Report validation passed; verdict remains PARTIELLEMENT CERTIFIE.')

"""Query OSV for public hosted package versions from both Dart lockfiles."""
import json
import os
from pathlib import Path
import urllib.request
import yaml

root=Path(__file__).resolve().parents[1]
packages={}
for app in ('mobile','admin'):
    lock=yaml.safe_load((root/f'apps/{app}/pubspec.lock').read_text(encoding='utf8'))
    for name,package in lock['packages'].items():
        if package['source']!='hosted': continue
        description=package['description']
        if not isinstance(description,dict) or description.get('url')!='https://pub.dev':
            raise SystemExit('Non-public hosted source needs separate review; refusing transmission')
        packages.setdefault((name,package['version']),[]).append(app)
queries=[{'package':{'name':name,'ecosystem':'Pub'},'version':version} for name,version in packages]
request=urllib.request.Request('https://api.osv.dev/v1/querybatch',
                              data=json.dumps({'queries':queries}).encode(),
                              headers={'Content-Type':'application/json','User-Agent':'EduNova-local-certification'})
with urllib.request.urlopen(request,timeout=60) as response:
    results=json.load(response)['results']
assert len(results)==len(queries), 'Incomplete OSV response'
findings=[]
incomplete=False
for (name,version),result in zip(packages,results):
    incomplete=incomplete or bool(result.get('next_page_token'))
    if result.get('vulns'):
        findings.append({'package':name,'version':version,'apps':packages[(name,version)],'advisories':result['vulns']})
record={'source':'https://api.osv.dev/v1/querybatch','ecosystem':'Pub','public_package_versions_checked':len(queries),
        'incomplete':incomplete,'findings':findings,'scope':'Hosted pub.dev packages only; excludes Flutter SDK and native transitive binaries'}
out=root/'evidence'/os.environ.get('EDUNOVA_CERT_EVIDENCE','phase19-final')/'pub-dependency-audit-results.json'
out.write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps(record,indent=2))
raise SystemExit(2 if incomplete else bool(findings))

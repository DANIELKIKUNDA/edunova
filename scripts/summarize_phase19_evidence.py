"""Summarize actual JUnit evidence; never infer success from absent output."""
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')

root = Path(__file__).resolve().parents[1]
out = root / 'evidence/local-phase19'
summaries = {}
for path in sorted(out.glob('*.xml')):
    document = ET.parse(path).getroot()
    cases = list(document.iter('testcase'))
    failures = []
    for case in cases:
        node = case.find('failure')
        if node is None:
            node = case.find('error')
        if node is not None:
            failures.append({'test': case.get('classname', '') + '::' + case.get('name', ''), 'message': node.get('message', ''), 'trace': node.text or ''})
    skipped = sum(case.find('skipped') is not None for case in cases)
    summaries[path.stem] = {'total': len(cases), 'passed': len(cases)-len(failures)-skipped, 'failed_or_error': len(failures), 'skipped': skipped, 'failures': failures}
(out / 'summary.json').write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding='utf-8')
for name, record in summaries.items():
    print(name, {k: v for k,v in record.items() if k != 'failures'})
    for failure in record['failures']:
        print('FAIL', failure['test'], failure['message'][:350])
for name in ('backend-final', 'mobile-analyze', 'mobile-test', 'mobile-web', 'admin-windows'):
    path = out / f'{name}.log'
    if path.exists():
        print('TAIL', name)
        print('\n'.join(path.read_text(encoding='utf-8', errors='replace').splitlines()[-5:]))

"""Report tracked publication risks without emitting matched secret values."""
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
patterns = {
    'private_key': rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'github_token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b',
    'aws_access_key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'stripe_live_key': rb'\bsk_live_[A-Za-z0-9]{20,}',
}
findings, oversized, forbidden = [], [], []
for name in filter(None, files):
    path = root/name
    if any(part in {'.local-certification', '.venv', 'build'} for part in Path(name).parts) or path.name == '.env':
        forbidden.append(name)
    if path.stat().st_size > 5_000_000:
        oversized.append({'path': name, 'bytes': path.stat().st_size})
    content = path.read_bytes()
    for kind, pattern in patterns.items():
        for match in re.finditer(pattern, content):
            findings.append({'path': name, 'line': content[:match.start()].count(b'\n')+1, 'kind': kind})
history=[]
objects=subprocess.check_output(['git','rev-list','--objects','6607b18da64eb44c2de017192ccefded21659a35..HEAD'],cwd=root,text=True).splitlines()
process=subprocess.Popen(['git','cat-file','--batch'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
try:
    for entry in objects:
        sha,_,name=entry.partition(' ')
        process.stdin.write((sha+'\n').encode()); process.stdin.flush()
        header=process.stdout.readline().decode().split()
        content=process.stdout.read(int(header[2])); process.stdout.read(1)
        if header[1]!='blob': continue
        for kind,pattern in patterns.items():
            if re.search(pattern,content): history.append({'blob':sha,'path':name,'kind':kind})
finally:
    process.stdin.close(); process.wait(timeout=30)
result = {'scope': 'tracked working-tree files and new Git history blobs; heuristic, not an exhaustive secret scanner',
          'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
          'findings_without_values': findings, 'historical_findings_without_values':history,
          'oversized_files': oversized, 'forbidden_files': forbidden}
out = root/'evidence/phase19-final/publication-inventory.json'
out.write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
raise SystemExit(bool(findings or history or forbidden))

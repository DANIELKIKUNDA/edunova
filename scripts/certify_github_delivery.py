"""Verify/update the authorized draft PR using existing Git credentials.

No token is written or printed. Never merges or changes draft state.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
URL='https://api.github.com/repos/DANIELKIKUNDA/edunova/pulls/1'

def token():
    env=os.environ.copy(); env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
    result=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',
                          cwd=ROOT,text=True,capture_output=True,env=env,timeout=30)
    if result.returncode: return None
    values=dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    return values.get('password')

def request(auth,body=None):
    headers={'Accept':'application/vnd.github+json','User-Agent':'EduNova-local-certification', 'X-GitHub-Api-Version':'2022-11-28'}
    if auth: headers['Authorization']='Bearer '+auth
    payload=json.dumps(body).encode() if body else None
    req=urllib.request.Request(URL,data=payload,headers=headers,method='PATCH' if body else 'GET')
    with urllib.request.urlopen(req,timeout=45) as response:
        return json.load(response)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--update-summary',type=Path)
    args=parser.parse_args(); auth=token(); pr=request(auth)
    if (pr['head']['ref'],pr['base']['ref'],pr['state'],pr['draft'],pr['merged']) != ('import/edunova-v0.57.12','main','open',True,False):
        raise SystemExit('PR state differs from authorized draft/main boundary; no update performed')
    if args.update_summary:
        if not auth: raise SystemExit('No existing Git credential available; PR not updated')
        start='<!-- EDUNOVA_LOCAL_PHASE19 -->'; end='<!-- /EDUNOVA_LOCAL_PHASE19 -->'
        body=pr.get('body') or ''
        if start in body:
            before,tail=body.split(start,1)
            if end not in tail: raise SystemExit('Unclosed certification marker; refusing body overwrite')
            body=before+tail.split(end,1)[1]
        body=body.rstrip()+'\n\n'+start+'\n'+args.update_summary.read_text(encoding='utf8')+'\n'+end
        pr=request(auth,{'body':body})
    result={'url':pr['html_url'],'state':pr['state'],'draft':pr['draft'],'merged':pr['merged'],
            'head_ref':pr['head']['ref'],'remote_head_sha':pr['head']['sha'],
            'base_ref':pr['base']['ref'],'summary_updated':bool(args.update_summary)}
    (ROOT/'evidence/phase19-final/publication.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()

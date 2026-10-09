"""Install built wheel without dependency resolution and run from outside source tree."""
from datetime import datetime, timezone
import json
import argparse
import tomllib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--dist',default=str(ROOT/'dist')); args=p.parse_args()
version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
wheels=list(Path(args.dist).glob(f'linux_opsec_auditor-{version}-py3-none-any.whl'))
assert len(wheels)==1, 'expected exactly one wheel'
with tempfile.TemporaryDirectory(prefix='opsec-wheel-') as temp:
    path=Path(temp)
    venv.create(path/'venv',with_pip=True)
    python=path/'venv/bin/python'
    clean=os.environ.copy(); clean.pop('PYTHONPATH',None)
    subprocess.run([str(python),'-m','pip','install','--no-index','--no-deps',str(wheels[0])],check=True,env=clean,cwd=temp)
    snap=json.loads((ROOT/'fixtures/healthy.json').read_text())
    snap['collected_at']=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    (path/'synthetic.json').write_text(json.dumps(snap))
    command=[str(path/'venv/bin/linux-opsec-auditor'),'audit','--input',str(path/'synthetic.json'),'--format','json']
    result=subprocess.run(command,check=True,capture_output=True,text=True,cwd=temp,env=clean,timeout=15)
    report=json.loads(result.stdout)
    assert report['summary']=={'pass':12,'fail':0,'unknown':0,'not_run':0}, report['summary']
    assert report['platform_validation']=='unverified_candidate'
    subprocess.run([str(path/'venv/bin/linux-opsec-auditor'),'--version'],check=True,cwd=temp,env=clean,timeout=15)
print('Smoke установленного wheel прошёл на synthetic input; поддержки платформ это не доказывает.')

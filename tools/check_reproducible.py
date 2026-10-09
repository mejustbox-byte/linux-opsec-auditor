"""Rebuild and compare wheel bytes with fixed SOURCE_DATE_EPOCH (same toolchain)."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
original=list((ROOT/'dist').glob('*.whl'))
assert len(original)==1
with tempfile.TemporaryDirectory(prefix='opsec-rebuild-') as temp:
    env=os.environ.copy(); env['SOURCE_DATE_EPOCH']='1791504000'
    subprocess.run([sys.executable,'-m','build','--wheel','--no-isolation','--outdir',temp],check=True,cwd=ROOT,env=env)
    rebuilt=list(Path(temp).glob('*.whl'))
    assert len(rebuilt)==1 and original[0].name==rebuilt[0].name
    assert original[0].read_bytes()==rebuilt[0].read_bytes(), 'wheel byte reproducibility failed'
    print('Wheel reproducibility passed; SHA256:',hashlib.sha256(original[0].read_bytes()).hexdigest())

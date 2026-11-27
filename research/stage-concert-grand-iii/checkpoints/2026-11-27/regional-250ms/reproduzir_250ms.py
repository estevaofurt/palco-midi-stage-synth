"""Reproduce regional 250ms comparisons in a clean sibling directory.
Default: both 250ms cases sequentially, independent audits. Use --regression
for exact 18ms comparison with hashes archived in stream-regression.json.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys
import numpy as np
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--regression',action='store_true');p.add_argument('--restart',action='store_true');p.add_argument('--ms',type=int,choices=[50,100,150,200,250],default=250);a=p.parse_args();a.regression=a.regression or a.restart
for line in (root/'PACOTE.sha256').read_text().splitlines():
    h,n=line.split(maxsplit=1)
    with (root/n).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
src=root/'G3_Controle_Repeticao';dst=root/('G3_Reproducao_Regional_'+('18ms' if a.regression else str(a.ms)+'ms'));dst.mkdir(exist_ok=False)
for f in [*src.glob('*.py'),src/'scale_geometry.json']:shutil.copy2(f,dst/f.name)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='2')
def run(script,args):
    with (dst/(script+'-'+('-'.join(args) or 'default')+'.log')).open('w') as f:subprocess.run([sys.executable,script,*args],cwd=dst,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
if a.regression:
    run('wet_250ms.py',['--ms','18','--rank','mixed']);ref=json.loads((src/'stream-regression.json').read_text());out=dst/'long-18ms-refined-384000-mixed-pedal'
    for k,x in ref['signals'].items():
        z=np.load(out/(k+'.npy'),mmap_mode='r',allow_pickle=False);assert list(z.shape)==x['shape'];h=hashlib.sha256()
        for i in range(0,len(z),1200):h.update(np.ascontiguousarray(z[i:i+1200]).tobytes())
        assert h.hexdigest()==x['sha256'],k
    print('Exact 18ms signal regression passed.')
    if a.restart:
        for args in [['--ms','18','--stop-step','1200'],['--ms','18','--resume','--stop-step','3200'],['--ms','18','--resume']]:run('wet_restart.py',args)
        run('verify_restart.py',[])
        print('Exact 18ms versioned restart regression passed.')
else:
    for rank in ['mixed','uniform']:run('wet_250ms.py',['--ms',str(a.ms),'--rank',rank])
    run('audit_250ms.py',['--ms',str(a.ms)])
print(dst)

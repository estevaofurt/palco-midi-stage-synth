"""Reproduce four 100 ms scenarios and two regional 18 ms scenarios in fresh directories."""
from pathlib import Path
import hashlib,shutil,subprocess,sys,os
root=Path(__file__).resolve().parent
for line in (root/'PACOTE.sha256').read_text().splitlines():
    h,n=line.split(maxsplit=1)
    with (root/n).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
src=root/'G3_Controle_Repeticao';ref=root/'G3_Reproducao_Referencia';dst=root/'G3_Reproducao_Controle'
if ref.exists() or dst.exists():raise SystemExit('Diretórios de reprodução já existem; preserve-os antes de repetir.')
for d in (ref,dst):
    d.mkdir()
    for p in [*src.glob('*.py'),src/'scale_geometry.json',src/'prefix-50ms.sha256.json']:shutil.copy2(p,d/p.name)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='2')
def run(cwd,name,*args):
    with (cwd/(name+'.log')).open('w') as log:subprocess.run([sys.executable,name,*map(str,args)],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
for name in ('wet_100ms.py','verify_events_100ms.py','verify_100ms.py','audit_100ms.py'):run(ref,name)
for name in ('wet_no_repeat.py','verify_no_repeat.py'):run(dst,name)
run(dst,'audit_repeat_effect.py',ref)
for name in ('audit_memory_support.py','audit_cavity_memory.py','audit_cavity_precision.py','check_regional.py','wet_regional.py','audit_regional_control.py'):run(dst,name)
print(dst)

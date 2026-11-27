"""Reproduce the three individual damper controls without overwriting the historical checkpoint.
Usage: python reproduzir_individual.py /path/to/G3_Sinais_Individuais.zip
The signal archive supplies immutable historical reference arrays and records.
"""
from pathlib import Path
import hashlib,os,shutil,subprocess,sys,zipfile
root=Path(__file__).resolve().parent
for line in (root/'PACOTE.sha256').read_text().splitlines():
    h,n=line.split(maxsplit=1)
    with (root/n).open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
src=root/'G3_Controle_Repeticao';dst=root/'G3_Reproducao_Individual'
if dst.exists():raise SystemExit('Preserve o diretório de reprodução existente antes de repetir.')
if len(sys.argv)!=2:raise SystemExit(__doc__)
dst.mkdir()
for p in [*src.glob('*.py'),src/'scale_geometry.json',src/'cavity-precision.json',src/'regional-control.json',src/'REFERENCE_REGIONAL.sha256']:shutil.copy2(p,dst/p.name)
with zipfile.ZipFile(sys.argv[1]) as z:
    for line in (dst/'REFERENCE_REGIONAL.sha256').read_text().splitlines():
        h,n=line.split(maxsplit=1);b=z.read(n);assert hashlib.sha256(b).hexdigest()==h,n;(dst/n).write_bytes(b)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='1')
for script,args in [('audit_modal_refinement.py',[]),('wet_individual.py',['33','55','72']),('audit_individual.py',[])]:
    with (dst/(script+'.log')).open('w') as f:subprocess.run([sys.executable,script,*args],cwd=dst,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
print(dst)

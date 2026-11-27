"""Reproduce opt-in modal candidate in a new directory; requires signal archive for historical references."""
from pathlib import Path
import hashlib,os,shutil,subprocess,sys,zipfile
root=Path(__file__).resolve().parent
for line in (root/'PACOTE.sha256').read_text().splitlines():
    h,n=line.split(maxsplit=1)
    with (root/n).open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==h,n
if len(sys.argv)!=2:raise SystemExit('Uso: python reproduzir_modal.py /caminho/G3_Sinais_Validacao_Modal.zip')
src=root/'G3_Controle_Repeticao';dst=root/'G3_Reproducao_Modal';dst.mkdir(exist_ok=False)
for p in [*src.glob('*.py'),src/'scale_geometry.json',src/'REFERENCE_REGIONAL.sha256']:shutil.copy2(p,dst/p.name)
with zipfile.ZipFile(sys.argv[1]) as z:
    for line in (dst/'REFERENCE_REGIONAL.sha256').read_text().splitlines():
        h,n=line.split(maxsplit=1);b=z.read(n);assert hashlib.sha256(b).hexdigest()==h,n;(dst/n).write_bytes(b)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='1')
for script,args in [('audit_modal_passivity.py',[]),('audit_all_modes.py',[]),('wet_modal_candidate.py',[]),('wet_modal_candidate.py',['--control','closed']),('wet_modal_candidate.py',['--rank','uniform']),('wet_modal_candidate.py',['--rate','192000']),('audit_modal_coupled.py',[])]:
    with (dst/(script+'-'+('-'.join(args) or 'default')+'.log')).open('w') as f:subprocess.run([sys.executable,script,*args],cwd=dst,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
print(dst)

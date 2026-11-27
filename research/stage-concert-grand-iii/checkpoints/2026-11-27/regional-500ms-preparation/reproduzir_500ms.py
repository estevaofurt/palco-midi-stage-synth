"""Run physical 500 ms experiment from the immutable 250 ms ZIP and this source folder.
Requires Python 3.11+, NumPy/SciPy/Numba, and at least 12 GiB free disk.
No network, no audio, no modification to the source archive.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,zipfile
EXPECTED='1d279241b7effc9704539c98987efd775eb937c369efcc2d3438354525570192'
HERE=Path(__file__).resolve().parent
NEW=('wet_500ms.py','wet_restart_500ms.py','audit_500ms.py','verify_prefix_250ms.py','verify_restart_500ms.py','SINAIS_250ms.sha256')
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    if not __debug__:raise RuntimeError('Assertions must be enabled')
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--workdir',type=Path,required=True);p.add_argument('--skip-restart',action='store_true');a=p.parse_args()
    package=a.package.resolve();work=a.workdir.resolve()
    assert digest(package)==EXPECTED,'Source package differs from archived checkpoint'
    assert not work.exists(),'Use a new working directory'
    assert work.parent.is_dir(),'Create the parent directory first'
    assert shutil.disk_usage(work.parent).free>=12*1024**3,'Insufficient disk; require 12 GiB'
    work.mkdir()
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        for member in z.infolist():
            target=(work/member.filename).resolve()
            assert target.is_relative_to(work),'Unsafe archive entry'
        z.extractall(work)
    manifests=list(work.rglob('PACOTE.sha256'));assert len(manifests)==1
    manifest=manifests[0];root=manifest.parent
    entries=manifest.read_text().splitlines();assert len(entries)==182
    for line in entries:
        h,n=line.split(maxsplit=1);f=(root/n).resolve();assert f.is_relative_to(root) and digest(f)==h,n
    src=root/'G3_Controle_Repeticao';dst=root/'G3_Regional_500ms';dst.mkdir()
    for f in [*src.glob('*.py'),src/'scale_geometry.json']:shutil.copy2(f,dst/f.name)
    for n in NEW:shutil.copy2(HERE/n,dst/n)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='2',PYTHONOPTIMIZE='0')
    def run(script,args):
        log=dst/(script+'-'+('-'.join(args) or 'default')+'.log')
        with log.open('x') as f:subprocess.run([sys.executable,script,*args],cwd=dst,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    for rank in ('mixed','uniform'):run('wet_500ms.py',['--ms','500','--rank',rank])
    run('audit_500ms.py',['--ms','500'])
    run('verify_prefix_250ms.py',[])
    physical=json.loads((dst/'long-500ms-audit.json').read_text())
    prefix=json.loads((dst/'prefix-250ms-of-500ms.json').read_text())
    assert len(physical['comparisons'])==10
    assert all(c['steps']==192000 and c['tail_after_200ms']['no_injection'] for c in physical['cases'].values())
    resume_gate=None
    if not a.skip_restart:
        for args in [['--stop-step','22000'],['--resume','--stop-step','96000'],['--resume','--stop-step','153600'],['--resume']]:run('wet_restart_500ms.py',['--ms','500',*args])
        run('verify_restart_500ms.py',[])
        resume_gate=json.loads((dst/'restart-500ms-regression.json').read_text())['gate']
    report=dict(physical_gate=bool(physical['final_gate'] and physical['all_prefix_gates']),prefix_gate=prefix['gate'],restart_gate=resume_gate,complete=False)
    report['complete']=bool(report['physical_gate'] and report['prefix_gate'] and resume_gate is True)
    (dst/'acceptance-500ms.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print(dst,report)
    if not report['complete']:raise SystemExit('Full acceptance not achieved (or restart was skipped); inspect reports')
if __name__=='__main__':main()

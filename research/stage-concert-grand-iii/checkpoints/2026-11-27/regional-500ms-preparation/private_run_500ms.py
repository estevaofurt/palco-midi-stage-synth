"""Private local execution of the original G3 500 ms experiment.

The ZIP remains on the user's machine. No upload, network access, or audio.
Receipts certify finished stages, not physical approval. Never deletes outputs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE=Path(__file__).resolve().parent
EXPECTED='1d279241b7effc9704539c98987efd775eb937c369efcc2d3438354525570192'
SIGNALS=('force','compression','velocity','flow','ledger')
NEW=('wet_500ms.py','wet_restart_500ms.py','audit_500ms.py','verify_prefix_250ms.py','verify_restart_500ms.py','SINAIS_250ms.sha256')
STOPS=(22000,96000,153600)
MIXED='long-500ms-refined-384000-mixed-pedal'
UNIFORM='long-500ms-refined-384000-uniform-pedal'
RESTART='restart-500ms-refined-384000-mixed-pedal'

def require(ok,message):
    if not ok:raise RuntimeError(message)

def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def atomic_json(p,obj):
    p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')
    tmp.replace(p)

def read_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def checked_path(root,name):
    p=(root/name).resolve()
    require(p.is_relative_to(root.resolve()),'Path escapes workspace: '+str(name))
    return p

def manifest_check(root):
    rows=(root/'PACOTE.sha256').read_text().splitlines()
    require(len(rows)==182,'Original manifest entry count changed')
    names=set()
    for line in rows:
        h,n=line.split(maxsplit=1)
        require(n not in names,'Duplicate original manifest entry: '+n)
        names.add(n)
        require(digest(checked_path(root,n))==h,'Original input changed: '+n)
    return digest(root/'PACOTE.sha256')

def prepare(package,work):
    require(not work.exists(),'Use a new workspace or --resume-work')
    require(digest(package)==EXPECTED,'Wrong original ZIP')
    require(work.parent.is_dir(),'Create parent directory first')
    require(shutil.disk_usage(work.parent).free>=12*1024**3,'At least 12 GiB free disk required')
    work.mkdir()
    with zipfile.ZipFile(package) as z:
        require(z.testzip() is None,'Corrupt ZIP')
        for member in z.infolist():checked_path(work,member.filename)
        z.extractall(work)
    roots=list(work.rglob('PACOTE.sha256'))
    require(len(roots)==1,'Expected one package manifest')
    root=roots[0].parent;mh=manifest_check(root)
    src=root/'G3_Controle_Repeticao';dst=root/'G3_Regional_500ms';dst.mkdir()
    for f in [*src.glob('*.py'),src/'scale_geometry.json']:shutil.copy2(f,dst/f.name)
    for n in NEW:shutil.copy2(HERE/n,dst/n)
    files={f.name:digest(f) for f in sorted(dst.iterdir()) if f.is_file()}
    atomic_json(work/'workspace.json',dict(package_sha256=EXPECTED,manifest_sha256=mh,root=str(root.relative_to(work)),sources=files,launcher_sha256=digest(Path(__file__))))
    return dst

def restore(work):
    m=read_json(work/'workspace.json')
    require(m['package_sha256']==EXPECTED,'Wrong workspace package')
    require(m['launcher_sha256']==digest(Path(__file__)),'Launcher changed; use the original revision')
    root=checked_path(work,m['root']);dst=root/'G3_Regional_500ms'
    require(manifest_check(root)==m['manifest_sha256'],'Manifest changed')
    for n,h in m['sources'].items():require(digest(checked_path(dst,n))==h,'Executor changed: '+n)
    require({p.name for p in dst.glob('*.py')}=={n for n in m['sources'] if n.endswith('.py')},'Unexpected Python module in workspace')
    return dst

def case_outputs(case):
    return [case+'.json',case+'/progress.json',*[case+'/'+k+'.npy' for k in SIGNALS]]

def snapshot_outputs(step):
    return [f'{RESTART}/restart-{step}.json',f'{RESTART}/restart-{step}.npz']

def stage_plan():
    return [
        ('mixed','wet_500ms.py',['--ms','500','--rank','mixed'],case_outputs(MIXED)),
        ('uniform','wet_500ms.py',['--ms','500','--rank','uniform'],case_outputs(UNIFORM)),
        ('audit','audit_500ms.py',['--ms','500'],['long-500ms-audit.json','long-500ms-pressure.npz',MIXED+'-audit.json',UNIFORM+'-audit.json']),
        ('prefix','verify_prefix_250ms.py',[],['prefix-250ms-of-500ms.json']),
        ('restart-22000','wet_restart_500ms.py',['--ms','500','--stop-step','22000'],snapshot_outputs(22000)),
        ('restart-96000','wet_restart_500ms.py',['--ms','500','--resume','--stop-step','96000'],snapshot_outputs(96000)),
        ('restart-153600','wet_restart_500ms.py',['--ms','500','--resume','--stop-step','153600'],snapshot_outputs(153600)),
        ('restart-final','wet_restart_500ms.py',['--ms','500','--resume'],case_outputs(RESTART)),
        ('restart-audit','verify_restart_500ms.py',[],['restart-500ms-regression.json'])
    ]

def receipt_check(dst,stage,outputs,receipt):
    require(receipt['stage']==stage and set(receipt['outputs'])==set(outputs),'Receipt mismatch: '+stage)
    for n,h in receipt['outputs'].items():
        require(digest(checked_path(dst,n))==h,'Completed output changed: '+n)

def run_stage(dst,spec,env,run=subprocess.run):
    stage,script,args,outputs=spec
    receipts=dst/'receipts';receipts.mkdir(exist_ok=True)
    receipt=receipts/(stage+'.json');log=receipts/(stage+'.log')
    if receipt.exists():
        receipt_check(dst,stage,outputs,read_json(receipt));return 'verified'
    # Do not destroy partial data or silently rerun an interrupted stage.
    require(not log.exists(),'Interrupted stage '+stage+'; preserve logs and inspect before retry')
    # The final restart deliberately reuses the preallocated NPY arrays
    # and progress record created by the three preceding checkpoint stages.
    reusable=set(case_outputs(RESTART)[1:]) if stage=='restart-final' else set()
    require(all(checked_path(dst,n).is_file() for n in reusable),'Missing preallocated restart signals')
    require(not any(checked_path(dst,n).exists() for n in outputs if n not in reusable),'Unreceipted output: '+stage)
    if stage in ('mixed','uniform','restart-22000'):
        case={'mixed':MIXED,'uniform':UNIFORM,'restart-22000':RESTART}[stage]
        require(not (dst/case).exists(),'Unreceipted case directory: '+case)
    with log.open('x',encoding='utf-8') as f:
        run([sys.executable,script,*args],cwd=dst,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    hashes={n:digest(checked_path(dst,n)) for n in outputs}
    atomic_json(receipt,dict(stage=stage,outputs=hashes))
    return 'executed'

def acceptance(dst):
    physical=read_json(dst/'long-500ms-audit.json')
    prefix=read_json(dst/'prefix-250ms-of-500ms.json')
    restart=read_json(dst/'restart-500ms-regression.json')
    p=bool(physical['final_gate'] and physical['all_prefix_gates'] and len(physical['comparisons'])==10 and all(v['causal_gate'] for v in physical['comparisons']) and len(physical['cases'])==2 and all(c['steps']==192000 and all(c['tail_after_200ms'][k] for k in ('no_injection','no_hammer_force','all_dampers_closed')) for c in physical['cases'].values()))
    q=bool(prefix['gate'] and len(prefix['files'])==10 and all(v['exact'] for v in prefix['files'].values()))
    r=bool(restart['gate'] and len(restart['signals'])==5 and [v['step'] for v in restart['snapshots']]==list(STOPS) and all(v['exact'] and all(v['snapshot_prefix_gates']) for v in restart['signals'].values()) and all(restart['metadata'].values()))
    return dict(physical_gate=p,prefix_gate=q,restart_gate=r,complete=p and q and r)

def main():
    require(__debug__,'Assertions must be enabled')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path)
    p.add_argument('--workdir',required=True,type=Path)
    p.add_argument('--resume-work',action='store_true')
    p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args();work=a.workdir.resolve()
    if a.resume_work:
        dst=restore(work)
    else:
        require(a.package is not None,'--package is required for a new workspace')
        dst=prepare(a.package.resolve(),work)
    print('Workspace:',dst,flush=True)
    if a.prepare_only:return
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',NUMBA_NUM_THREADS='2',PYTHONOPTIMIZE='0')
    for spec in stage_plan():print(spec[0],run_stage(dst,spec,env),flush=True)
    report=acceptance(dst);atomic_json(dst/'acceptance-500ms.json',report);print(report,flush=True)
    if not report['complete']:raise SystemExit('Physical acceptance failed; preserve results')
if __name__=='__main__':main()

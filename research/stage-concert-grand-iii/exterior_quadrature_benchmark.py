"""Controlled benchmark on actual cabinet panels.
Each variant runs in an independent process to measure Linux peak RSS.
Only timing and resource use are experimental; numerical equivalence is gated.
"""
import argparse,hashlib,json,resource,statistics,subprocess,sys,time
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from lid_exterior import self_react
from exterior_self_stream import self_react_blocked
from exterior_pair_stream import pair_integrals
from split_radiation import relative
ROOT=Path(__file__).parent
FREQ=[30.,80.,150.,200.,250.,300.]
def read(n):return json.loads((ROOT/n).read_text())

def panels(scale,angle):
    raw=scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    field=lambda x:np.ones((len(x),1))
    _,p,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],angle,36,field,36)
    assert geo['gate'] and len(p)==7
    return p,hashlib.sha256(raw).hexdigest()

def direct_pair(x,A,y,B,k):
    D=cdist(x,y);assert D.min()>0
    return (np.stack([A.T@(np.sinc(kl*D/np.pi)@B) for kl in k]),
        np.stack([A.T@((np.cos(kl*D)/D)@B) for kl in k]))

def worker(a):
    p,sha=panels(a.scale,a.angle);k=2*np.pi*np.asarray(FREQ)/343.
    if a.case=='self-mouth':i=6;other=None
    elif a.case=='self-small':i=min(range(6),key=lambda j:p[j].basis.area);other=None
    else:i=6;other=max(range(6),key=lambda j:p[j].basis.area)
    panel=p[i]
    if other is None:
        s=panel.samples(14);inner=24
        fn=(lambda:self_react(panel,s,k,inner)[None]) if a.block==0 else (lambda:self_react_blocked(panel,s,k,inner,block=a.block)[None])
        detail=dict(panel=i,outer=14,inner=inner,targets=len(s[0]),modes=36)
    else:
        _,x,w,S=panel.samples(24);_,y,v,T=p[other].samples(24);A=w[:,None]*S;B=v[:,None]*T
        fn=(lambda:np.stack(direct_pair(x,A,y,B,k))) if a.block==0 else (lambda:np.stack(pair_integrals(x,A,y,B,k,mutual=True,block=a.block)[:2]))
        detail=dict(panel=i,otherPanel=other,outer=24,targets=len(x),sources=len(y),modes=36,
            distanceBytes=min(a.block or len(x),len(x))*len(y)*8)
    # Same inputs, one untimed warmup and two timed repetitions per process.
    first=fn();times=[];errors=[]
    for _ in range(2):
        t=time.perf_counter();z=fn();times.append(time.perf_counter()-t)
        errors.append(relative(z,first))
    assert max(errors)<=1e-11 and np.isfinite(z).all()
    np.save(a.out/'result.npy',z,allow_pickle=False)
    report=dict(case=a.case,angleDeg=a.angle,block=a.block,scaleSha256=sha,
        medianSeconds=statistics.median(times),seconds=times,repeatRelative=max(errors),
        peakRssBytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),**detail)
    (a.out/'worker.json').write_text(json.dumps(report,indent=2,allow_nan=False))

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True)
    p.add_argument('--case',choices=['self-mouth','self-small','pair-mouth']);p.add_argument('--block',type=int)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    if a.case is not None:
        if a.block is None or a.block<0:raise ValueError('invalid worker block')
        worker(a);return
    rows=[];path=a.out/'exterior_quadrature_benchmark.json'
    for case,blocks in [('self-mouth',[0,4,8,16]),('self-small',[0,4,8,16]),('pair-mouth',[0,64,128,256])]:
        ref=None;baseline=None
        for block in blocks:
            d=a.out/f'{case}_{block}';d.mkdir(exist_ok=True)
            subprocess.run([sys.executable,str(Path(__file__).resolve()),'--scale',str(a.scale.resolve()),'--out',str(d.resolve()),
                '--angle',str(a.angle),'--case',case,'--block',str(block)],check=True)
            r=json.loads((d/'worker.json').read_text());z=np.load(d/'result.npy',allow_pickle=False)
            if ref is None:ref=z;baseline=r
            assert r['scaleSha256']==baseline['scaleSha256']
            r.update(equivalence=relative(z,ref),speedup=baseline['medianSeconds']/r['medianSeconds'],
                peakRssRelative=r['peakRssBytes']/baseline['peakRssBytes'])
            r['gate']=r['equivalence']<=1e-11
            rows.append(r);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
            print('G3_QUADRATURE_BENCH_CASE '+json.dumps(r),flush=True);assert r['gate']
    summary=dict(gate=all(r['gate'] for r in rows),angleDeg=a.angle,diagnosticOnly=True,representativePanelsOnly=True,
        independentProcesses=True,peakRssIncludesInterpreter=True,frequenciesHz=FREQ,fullLoadBenchmark=False,
        fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=rows[0]['scaleSha256']),indent=2,allow_nan=False))
    print('G3_QUADRATURE_BENCH_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()

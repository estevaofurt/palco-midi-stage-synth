"""Independent representative quadrature convergence for 55-mode ports.
No FEM solve, symmetrization or changes to the running reference.
Report the raw reactive and resistive-kernel blocks in their common basis.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from exterior_self_stream import self_react_blocked
from exterior_pair_stream import pair_integrals
from acoustic_port_bridge import vertices
from split_radiation import relative
ROOT=Path(__file__).parent
FREQ=[30.,80.,150.,200.,250.,300.]
LIMIT=.01
def read(n):return json.loads((ROOT/n).read_text())

def changes(old,new):
    old,new=map(np.asarray,(old,new))
    if old.shape!=new.shape or old.ndim!=3 or old.shape[0]!=len(FREQ) or not all(np.isfinite(x).all() for x in (old,new)):
        raise ValueError('incompatible quadrature blocks')
    # Each frequency has its own reference norm. Do not let a strong
    # high-frequency response mask an error at low frequency.
    return [dict(frequencyHz=f,relative=relative(a,b)) for f,a,b in zip(FREQ,old,new)]

def self_metrics(x):
    return [dict(frequencyHz=f,rawAsymmetry=relative(a,a.T)) for f,a in zip(FREQ,x)]

def adjacent(p,i):
    x=vertices(p[i]);candidates=[]
    for j in range(6):
        if j==i:continue
        d=cdist(x,vertices(p[j]))
        # Shared physical edge, not a merely nearby disconnected panel.
        if np.sum(d.min(1)<1e-9)>=2:candidates.append(j)
    if not candidates:raise ValueError('no adjacent upper panel')
    return min(candidates,key=lambda j:p[j].basis.area)

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,lambda x:np.ones((len(x),1)),55)
    assert geo['gate'] and len(ports)==7 and all(x.basis.count==55 for x in ports)
    i=min(range(6),key=lambda j:ports[j].basis.area);j=adjacent(ports,i);large=max(range(6),key=lambda j:ports[j].basis.area)
    k=2*np.pi*np.asarray(FREQ)/343.
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'high_mode_quadrature.json'
    rows=[];arrays={}
    def checkpoint():
        path.write_text(json.dumps(dict(cases=rows,scaleSha256=sha,complete=False),indent=2,allow_nan=False))
    for name,idx in [('self-small',i),('self-mouth',6)]:
        results=[]
        for outer,inner in [(30,52),(30,64),(36,64)]:
            t=time.perf_counter();s=ports[idx].samples(outer)
            X=self_react_blocked(ports[idx],s,k,inner,block=8)
            assert X.shape==(len(FREQ),55,55) and np.isfinite(X).all()
            results.append(X);arrays[f'{name}_{outer}_{inner}']=X
            row=dict(case=name,panel=idx,outer=outer,inner=inner,seconds=time.perf_counter()-t,
                frequencies=self_metrics(X))
            rows.append(row);checkpoint()
            print('G3_HIGH_QUAD_CASE '+json.dumps(row),flush=True)
        source=changes(results[0],results[1]);target=changes(results[1],results[2]);joint=changes(results[0],results[2])
        maximum=max(x['relative'] for seq in (source,target,joint) for x in seq)
        asym=max(v['rawAsymmetry'] for v in self_metrics(results[-1]))
        row=dict(case=name,kind='self-comparison',source=source,target=target,joint=joint,
            maximumRelative=maximum,maximumFineRawAsymmetry=asym,quadratureGate=bool(maximum<=LIMIT and asym<=.001))
        rows.append(row);checkpoint();print('G3_HIGH_QUAD_COMPARISON '+json.dumps(row),flush=True)
    for name,i0,i1 in [('pair-adjacent',i,j),('pair-mouth',6,large)]:
        results=[]
        for order in (30,36,42):
            t=time.perf_counter()
            _,x,w,V=ports[i0].samples(order);_,y,v,T=ports[i1].samples(order)
            R,X,r=pair_integrals(x,w[:,None]*V,y,v[:,None]*T,k,mutual=True,block=64)
            assert R.shape==X.shape==(len(FREQ),55,55) and np.isfinite(R).all() and np.isfinite(X).all()
            results.append((R,X));arrays[f'{name}_R_{order}']=R;arrays[f'{name}_X_{order}']=X
            row=dict(case=name,panel=i0,otherPanel=i1,outer=order,seconds=time.perf_counter()-t,**r)
            rows.append(row);checkpoint();print('G3_HIGH_QUAD_CASE '+json.dumps(row),flush=True)
        comparison={}
        for key,n in [('resistiveKernel',0),('reactiveKernel',1)]:
            comparison[key]=dict(coarseToMid=changes(results[0][n],results[1][n]),
                midToFine=changes(results[1][n],results[2][n]),coarseToFine=changes(results[0][n],results[2][n]))
        maximum=max(v['relative'] for block in comparison.values() for seq in block.values() for v in seq)
        row=dict(case=name,kind='mutual-comparison',**comparison,maximumRelative=maximum,quadratureGate=bool(maximum<=LIMIT))
        rows.append(row);checkpoint();print('G3_HIGH_QUAD_COMPARISON '+json.dumps(row),flush=True)
    comps=[r for r in rows if 'quadratureGate' in r];assert len(comps)==4
    np.savez_compressed(a.out/'high_mode_quadrature_blocks.npz',frequencies=FREQ,**arrays)
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,representativePanelsOnly=True,modesPerPanel=55,
        frequenciesHz=FREQ,maximumRelative=max(r['maximumRelative'] for r in comps),
        representativeQuadratureGate=all(r['quadratureGate'] for r in comps),quadratureLimit=LIMIT,
        angularQuadratureCertified=False,fullExteriorQuadratureCertified=False,modalConvergenceCertified=False,
        fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_HIGH_QUAD_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()

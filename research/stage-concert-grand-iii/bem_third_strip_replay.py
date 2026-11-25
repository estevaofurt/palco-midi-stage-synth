"""Re-localize the solved 650-budget mesh at 80 Hz without a new fit.
Create conforming third-generation strip candidates only after independent
band integration and archived power/geometry checks pass.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import velocities
from bem_edge_localization import inventory,localize
from bem_strip_band_replay import compare_bands
from bem_edge_strip import budget_strips
from bem_candidate_guard import validate_candidate
from bem_mesh_guard import signature
from bem_power_partition import partition
from bem_strip_audit import reliable
from exterior_bem import topology
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def validate_source(doc,arrays,angle,sha):
    s=doc.get('summary',{});rows=doc.get('cases',[])
    if doc.get('scaleSha256')!=sha or any(s.get(k)!=v for k,v in dict(gate=True,angleDeg=angle,frequencyHz=80.,diagnosticOnly=True,solverApproved=False,radiationReady=False).items()):
        raise ValueError('invalid candidate source')
    if s.get('geometry',{}).get('gate') is not True or not isinstance(s.get('physicalGate'),bool) or [(r.get('outerOrder'),r.get('innerOrder')) for r in rows]!=[(6,8),(8,8),(8,10)]:
        raise ValueError('incomplete candidate evidence')
    if not all(reliable(s[k]) for k in ('targetConvergence','sourceConvergence')) or not 0<=s['farConvergence']<=.01:
        raise ValueError('unreliable source quadrature')
    t,l,q=(arrays[k] for k in ('triangles','labels','density'))
    if len(t)!={30:628,55:626}[angle] or l.shape!=(len(t),) or not np.issubdtype(l.dtype,np.integer) or q.ndim!=2 or q.shape[0]!=3*len(t):
        raise ValueError('invalid candidate arrays')
    if not all(np.isfinite(x).all() for x in arrays.values()) or not topology(t)['gate']:
        raise ValueError('invalid mesh or density')
    sig=signature(t,l);qs=hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()
    for x in [s,*rows]:
        if x.get('meshSha256')!=sig or x.get('densitySha256')!=qs:raise ValueError('source signature mismatch')
    if any(x.get('elements')!=len(t) or x.get('frequencyHz')!=80 for x in rows):raise ValueError('source case mismatch')
    ar=rows[-1]['audit'];m=q.shape[1]
    if any(arrays[k].shape!=(m,m) for k in ('prescribed','computed','radiation')) or arrays['pressure'].ndim!=2 or arrays['pressure'].shape[1]!=m:
        raise ValueError('invalid source work arrays')
    part=partition(arrays['prescribed'],arrays['computed'],arrays['radiation'])
    for k in ('totalPowerRelative','boundaryWorkRelative','computedWorkRelative','partitionClosure'):
        if abs(part[k]-ar[k])>1e-10*max(1,abs(ar[k])):raise ValueError('source work mismatch')
    return ar

def mark_scores(rep,classes):
    a=np.asarray(rep['sectorBandIndicator'],float)
    if a.shape!=(*classes.shape,3) or not np.isfinite(a).all() or np.any(a<0):raise ValueError('invalid band indicators')
    return a[:,:,0],np.isin(classes,['crease','crease-port-transition'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'bem_candidate.json').read_text())
    with np.load(a.archive/'candidate_matrices.npz',allow_pickle=False) as z:
        arrays={k:z[k] for k in ('triangles','labels','density','prescribed','computed','radiation','pressure')}
    ar=validate_source(doc,arrays,a.angle,sha);t,l,q=(arrays[k] for k in ('triangles','labels','density'))
    ll=layout_build(sc,read('layout_hypothesis.json'));c=contour_build(ll,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(c['contourXY_m']);g=geometry(poly,ll,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    surf,ports,center=envelope(poly,g['rimTopZ_m'],a.angle,3,field);geo=geometry_audit(surf,ports,center)
    assert geo['gate'] and abs(topology(t)['volume']-geo['volume'])<=1e-10
    kinds=[s['kind'] for s in surf];classes,_=inventory(t,l,kinds)
    v=lambda x,o:velocities(surf,ports,x,l[o]);k=2*np.pi*80/343.
    assert v(t.mean(1),np.arange(len(t))).shape==(len(t),q.shape[1])
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_third_strip_replay.json';rows=[]
    for order in (3,5):
        rr=localize(t,l,kinds,q,v,k,order,8,exact_bands=True)
        assert rr['energyClosure']<=1e-10
        np.testing.assert_allclose(np.sum([x['bandAreaFractions'] for x in rr['categories']],axis=0),[.19,.45,.36],atol=1e-10)
        np.testing.assert_allclose(np.asarray(rr['sectorBandIndicator']).sum(2),rr['sectorIndicator'],atol=1e-12)
        rows.append(rr);path.write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_THIRD_STRIP_CASE '+json.dumps({k:v for k,v in rr.items() if k not in ('elementIndicator','sectorIndicator','sectorBandIndicator')}),flush=True)
    change=compare_bands(*rows);diff={k:abs(rows[-1][k]-ar[k])/max(ar[k],1e-30) for k in ('heldoutResidual','heldoutWorstColumn')}
    gate=bool(change['gate'] and max(diff.values())<=.05);entries=[]
    if gate:
        S,M=mark_scores(rows[-1],classes)
        for budget in (850,1050):
            tt,lab,parents,rep=budget_strips(t,l,S,M,budget)
            name=f'third_strip_{budget}.npz';entry=dict(file=name,meshSha256=signature(tt,lab),**rep)
            entry['geometryAudit']=validate_candidate(t,l,tt,lab,parents,entry,budget)
            np.savez_compressed(a.out/name,triangles=tt,labels=lab,parents=parents)
            entries.append(entry)
    categories=[x for x in rows[-1]['categories'] if x['kind'] in ('crease','crease-port-transition')]
    summary=dict(gate=gate,angleDeg=a.angle,frequencyHz=80.,diagnosticOnly=True,fixedDensity=True,sourceElements=len(t),
        sourceMeshSha256=doc['summary']['meshSha256'],sourceDensitySha256=doc['summary']['densitySha256'],
        convergence=change,againstArchivedAudit=diff,creaseEnergyFraction=sum(x['residualEnergyFraction'] for x in categories),
        nearCreaseEnergyFraction=sum(x['bandEnergyFractions'][0] for x in categories),nearCreaseAreaFraction=sum(x['bandAreaFractions'][0] for x in categories),
        candidateMeshes=entries,physicalGate=False,solverApproved=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_THIRD_STRIP_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()

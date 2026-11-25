"""Replay the audited 80 Hz strip density without another BEM fit.
Exact radial band localization and geometry-only candidates for refinement.
The new candidate meshes are not acoustic solutions.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import velocities
from bem_edge_localization import inventory,localize
from bem_edge_strip import budget_strips
from bem_mesh_guard import signature
from bem_power_partition import partition
from bem_strip_audit import reliable
from exterior_bem import topology
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def validate_archive(doc,arrays,angle,sha):
    s=doc.get('summary',{});rows=doc.get('cases',[])
    if doc.get('scaleSha256')!=sha or s.get('angleDeg')!=angle or s.get('frequencyHz')!=80 or s.get('gate') is not True:
        raise ValueError('wrong or incomplete 80 Hz source proof')
    if any(s.get(k) is not v for k,v in dict(diagnosticOnly=True,fixedMesh=True,fixedDensity=True,solverApproved=False,radiationReady=False).items()):
        raise ValueError('invalid diagnostic scope')
    if len(rows)!=3 or [(x.get('outerOrder'),x.get('innerOrder')) for x in rows]!=[(6,8),(8,8),(8,10)]:
        raise ValueError('wrong source quadrature')
    if not all(reliable(s[k]) for k in ('targetConvergence','sourceConvergence')) or not 0<=s['farConvergence']<=.01:
        raise ValueError('source quadrature not converged')
    t,l,q=arrays['triangles'],arrays['labels'],arrays['density']
    sig=signature(t,l);density=hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()
    if len(t)!=(444 if angle==30 else 446) or not np.issubdtype(l.dtype,np.integer) or q.ndim!=2 or q.shape[0]!=3*len(t):
        raise ValueError('wrong source geometry or density')
    if not all(np.isfinite(x).all() for x in arrays.values()) or not topology(t)['gate']:
        raise ValueError('invalid archive arrays')
    for x in [s,*rows]:
        if x.get('meshSha256')!=sig or x.get('densitySha256')!=density:
            raise ValueError('archive signature mismatch')
    if any(x.get('frequencyHz')!=80 or x.get('elements')!=len(t) for x in rows):
        raise ValueError('archive case mismatch')
    ar=rows[-1]['audit'];part=partition(arrays['prescribed'],arrays['computed'],arrays['radiation'])
    if arrays['prescribed'].shape!=(q.shape[1],q.shape[1]) or any(abs(part[k]-ar[k])>1e-10*max(1,abs(ar[k])) for k in ('totalPowerRelative','boundaryWorkRelative','computedWorkRelative','partitionClosure')):
        raise ValueError('archived work mismatch')
    return ar

def compare_bands(a,b):
    if [x['kind'] for x in a['categories']]!=[x['kind'] for x in b['categories']]:
        raise ValueError('incompatible category inventory')
    res={k:abs(a[k]-b[k])/max(b[k],1e-30) for k in ('heldoutResidual','heldoutWorstColumn')}
    band=max(float(np.max(abs(np.asarray(x['bandEnergyFractions'])-y['bandEnergyFractions']))) for x,y in zip(a['categories'],b['categories']))
    indicator=relative(np.asarray(a['sectorBandIndicator']),np.asarray(b['sectorBandIndicator']))
    return dict(**res,bandEnergyFractionAbsolute=band,indicatorRelative=indicator,
        gate=max(res.values())<=.05 and band<=.02 and indicator<=.05)

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'bem_strip_audit.json').read_text())
    with np.load(a.archive/'strip_matrices.npz',allow_pickle=False) as z:
        arrays={k:z[k] for k in ('triangles','labels','density','prescribed','computed','radiation','pressure')}
    ar=validate_archive(doc,arrays,a.angle,sha);t,l,q=(arrays[k] for k in ('triangles','labels','density'))
    ll=layout_build(sc,read('layout_hypothesis.json'));c=contour_build(ll,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(c['contourXY_m']);g=geometry(poly,ll,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    surf,ports,center=envelope(poly,g['rimTopZ_m'],a.angle,3,field);geo=geometry_audit(surf,ports,center);assert geo['gate']
    assert abs(topology(t)['volume']-geo['volume'])<=1e-10
    kinds=[s['kind'] for s in surf];classes,_=inventory(t,l,kinds)
    v=lambda x,o:velocities(surf,ports,x,l[o]);k=2*np.pi*80/343.
    assert v(t.mean(1),np.arange(len(t))).shape==(len(t),q.shape[1])
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_strip_band_replay.json';rows=[]
    for order in (3,5):
        r=localize(t,l,kinds,q,v,k,order,8,exact_bands=True)
        assert r['energyClosure']<=1e-10
        area=np.sum([x['bandAreaFractions'] for x in r['categories']],axis=0)
        np.testing.assert_allclose(area,[.19,.45,.36],atol=1e-10)
        np.testing.assert_allclose(np.asarray(r['sectorBandIndicator']).sum(2),r['sectorIndicator'],atol=1e-12)
        rows.append(r);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_STRIP_BAND_CASE '+json.dumps({key:val for key,val in r.items() if key not in ('elementIndicator','sectorIndicator','sectorBandIndicator')}),flush=True)
    change=compare_bands(*rows)
    auditDifference={k:abs(rows[-1][k]-ar[k])/max(ar[k],1e-30) for k in ('heldoutResidual','heldoutWorstColumn')}
    gate=bool(change['gate'] and max(auditDifference.values())<=.05)
    candidates=[]
    if gate:
        # Near-band residual is a marking indicator, not a claim of an optimal mesh.
        score=np.asarray(rows[-1]['sectorBandIndicator'])[:,:,0]
        eligible=np.isin(classes,['crease','crease-port-transition'])
        for budget in (650,850):
            tt,lab,parents,rep=budget_strips(t,l,score,eligible,budget)
            assert len(tt)<=budget and abs(topology(tt)['volume']-geo['volume'])<=1e-10
            name=f'candidate_{budget}.npz';np.savez_compressed(a.out/name,triangles=tt,labels=lab,parents=parents)
            candidates.append(dict(file=name,meshSha256=signature(tt,lab),**rep))
    summary=dict(gate=gate,angleDeg=a.angle,frequencyHz=80.,diagnosticOnly=True,fixedDensity=True,
        meshSha256=doc['summary']['meshSha256'],densitySha256=doc['summary']['densitySha256'],
        convergence=change,againstArchivedAudit=auditDifference,candidateMeshes=candidates,
        physicalGate=False,solverApproved=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_STRIP_BAND_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()

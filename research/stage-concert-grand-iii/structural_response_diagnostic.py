"""Replay failed structural cases with diagnostic and energy-conditioned solver.
Preserve original tests and tolerances; record all cases even if gates fail.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from rim_structure import assemble as rim_assemble
from structural_assembly import assemble as structure
from structural_response import response
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def compare(a,b,units):
    x=a*units[:,None]*units[None,:];y=b*units[:,None]*units[None,:]
    e=float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30))
    return dict(relative=e,gate=e<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--case',choices=['rim','structure'],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json');rc=read('rim_structure_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.array(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    pts=np.array([l['bridgeAttachmentNodes'][s][len(l['bridgeAttachmentNodes'][s])//2]['footProjectionXYZ_m'][:2] for s in ('bass','treble')]+[c['centroidXY_m']])
    freq=np.geomspace(30,150,24);rows=[];Y=[];cache=None;old=None
    if a.case=='rim':
        cases=[(12,8,14,True),(18,8,14,True),(24,8,14,True),(30,8,14,True),(30,8,18,True)];units=np.ones(4)
    else:
        cases=[(12,2,12,True),(18,2,12,True),(24,2,12,True),(30,2,12,True),(30,4,12,True),(30,4,16,True),(30,4,16,False)];units=np.array([1.,.02,1.,.02,1.,1.])
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'structural_conditioning.json'
    for cells,sub,order,connected in cases:
        if old!=cells:
            cache=assemble(poly,c['ribs'],mat['plate'],rib,cells,14,False);old=cells
        m=cache
        assert m['rank']==m['fullRank']
        if a.case=='rim':
            z=rim_assemble(m,rc,sub,order,connected);n=z['plateDofs'];P=np.zeros((len(z['M']),4))
            P[:n,:3]=(m['basis'].evaluate(pts)[0]@m['T']).T;P[n,3]=1.
            K=z['K']+z['J']
        else:
            z=structure(m,centers,read('bridge_hypothesis.json'),mat,rc,sub,8,order,connected)
            P=z['P'];K=z['K']+z['Jrim']+z['Jbridge']
        record=dict(cells=cells,sub=sub,order=order,connected=connected,dofs=len(K),plateRank=m['rank'],condition=m['condition'])
        try:
            direct,ds,dr=response(z['M'],K,z['D'],P,freq,units,'direct')
            record.update(direct=ds,directPerFrequency=dr)
        except Exception as e:
            direct=None;record['directError']=str(e)
        try:
            y,s,d=response(z['M'],K,z['D'],P,freq,units)
            Y.append(y);record.update(energy=s,energyPerFrequency=d)
            if direct is not None:record['solverComparison']=compare(direct,y,units)
            cross=float(np.max(abs(y[:,-1,:-1]))) if a.case=='rim' else float(np.max(abs(y[:,0,2])))
            record['crossMobilityMaxMsN']=cross;record['crossGate']=bool(cross>0 if connected else cross<1e-14)
        except Exception as e:
            Y.append(None);record['energyError']=str(e)
        rows.append(record)
        # Write partial results immediately, even when subsequent refinement fails.
        path.write_text(json.dumps(dict(case=a.case,cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_CONDITION_CASE '+json.dumps({k:v for k,v in record.items() if not k.endswith('PerFrequency')}),flush=True)
    count=len(cases) if a.case=='rim' else len(cases)-1
    checks=[compare(x,y,units) if x is not None and y is not None else dict(relative=None,gate=False) for x,y in zip(Y[:count-1],Y[1:count])]
    gate=all(q.get('energy',{}).get('gate',False) and q.get('crossGate',False) for q in rows) and all(q['gate'] for q in checks[-(2 if a.case=='rim' else 3):])
    summary=dict(case=a.case,convergence=checks,gate=gate,boardReady=False,rimReady=False,complete=True)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_CONDITION_GATE '+json.dumps(summary),flush=True);assert gate,'conditioning or convergence'
if __name__=='__main__':main()

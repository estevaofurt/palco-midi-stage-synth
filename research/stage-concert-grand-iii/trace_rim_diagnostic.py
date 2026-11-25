"""Independent essential trace and mobile rim diagnostics."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from spline_plate import assemble
from trace_plate import constrained
from ribbed_plate import response
from ribbed_plate_diagnostic import compare
from rim_structure import assemble as rim_assemble,response as rim_response
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--case',choices=['trace','rim'],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rc=read('ribbed_plate_hypothesis.json')
    poly=np.array(c['contourXY_m']);pts=np.array([l['bridgeAttachmentNodes'][s][len(l['bridgeAttachmentNodes'][s])//2]['footProjectionXYZ_m'][:2] for s in ('bass','treble')]+[c['centroidXY_m']])
    freq=np.geomspace(30,150,24);cases=[];results=[]
    if a.case=='trace':
        for cells,order in [(12,14),(18,14),(24,14),(30,14),(30,18)]:
            m=constrained(poly,c['ribs'],mat['plate'],rc['rib'],cells,order)
            f,y=response(m,pts,freq,mat['plate'],True);b,_=response(m,pts,freq,mat['plate'],False)
            results.append((f,y));cases.append(dict(cells=cells,order=order,rank=m['rank'],fullRank=m['fullRank'],
                constrainedRank=m['constrainedRank'],constraintRank=m['constraintRank'],traceResidual=m['traceResidual'],independentTraceResidual=m['independentTraceResidual'],
                first8BareHz=b[:8].tolist(),first8RibbedHz=f[:8].tolist(),condition=m['condition']))
        checks=[compare(x,y) for x,y in zip(results,results[1:])]
        gate=checks[-2]['gate'] and checks[-1]['gate'] and all(q['rank']==q['fullRank'] for q in cases)
    else:
        cfg=read('rim_structure_hypothesis.json')
        for cells,sub,order,connected in [(9,4,12,True),(12,4,12,True),(12,8,12,True),(12,8,16,True),(12,8,16,False)]:
            m=assemble(poly,c['ribs'],mat['plate'],rc['rib'],cells,14,False)
            z=rim_assemble(m,cfg,sub,order,connected);cholesky(z['M'])
            if connected:cholesky(z['K']+z['J'])
            y,rec,pas=rim_response(m,z,pts,freq);results.append(y)
            cross=float(np.max(abs(y[:,-1,:-1])))
            assert cross>0 if connected else cross<1e-14
            cases.append(dict(cells=cells,sub=sub,order=order,connected=connected,rimMassKg=z['rimMassKg'],plateDofs=z['plateDofs'],rimDofs=z['rimDofs'],
                crossMobilityMaxMsN=cross,reciprocity=rec,passivityMinRelative=pas))
        checks=[]
        for x,y in zip(results[:3],results[1:4]):
            e=float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30));checks.append(dict(relative=e,gate=e<=.05))
        gate=all(q['gate'] for q in checks)
    summary=dict(case=a.case,cases=cases,convergence=checks,gate=gate,boardReady=False,rimReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'trace_rim.json').write_text(json.dumps(dict(summary=summary,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_TRACE_RIM_GATE '+json.dumps(summary),flush=True);assert gate,'trace or rim convergence'
if __name__=='__main__':main()

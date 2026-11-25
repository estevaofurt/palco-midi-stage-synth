"""Independent low-band wet strings and dry higher-band modal convergence.
Do not use as a substitute for full-coordinate G3.05h residual validation.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from structural_response import response as direct
from string_structure import setup,response as full_strings
from polygon_radiation import modes,SurfaceModes
from split_radiation import split_load,relative
from modal_string_radiation import response,truncate
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--case',choices=['wet','band'],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.array(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    m=assemble(poly,c['ribs'],mat['plate'],rib,30,14,False)
    z=structure(m,centers,read('bridge_hypothesis.json'),mat,read('rim_structure_hypothesis.json'),2,8,14,True)
    M=z['M'];K=z['K']+z['Jrim']+z['Jbridge'];D=z['D']
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'modal_string_radiation.json'
    cases=[];checks=[]
    if a.case=='band':
        P=z['P'][:,[0,2,4,5]];freq=np.geomspace(30,500,32)
        q=modes(M,K,D,P,256);ref,ds,_=direct(M,K,D,P,freq,np.ones(4))
        for n in (64,128,192,256):
            mm=truncate(q,n);Y=[response(mm,[],[],np.zeros((n,n)),np.zeros((2,n)),f)[0] for f in freq]
            cases.append(dict(modes=n,highestModeHz=float(q['Hz'][n-1]),relative=relative(Y,ref)))
        gate=ds['gate'] and cases[-1]['relative']<=.05
        extra=dict(dryReference=ds)
    else:
        rr={r['key']:r for r in sc['rows']};keys=[45,48];P,wires,labels=setup(z,centers,rr,keys,2,128)
        freq=np.array([30.,50.,80.,110.,130.8128,150.]);q=modes(M,K,D,P,96)
        dry,ds,_=full_strings(M,K,D,P,wires,freq)
        mic=np.array([x['xyzM'] for x in l['capture']]);field=SurfaceModes(m,q['U'][:z['plateDofs']])
        outputs=[]
        for outer,inner,angle in [(18,28,20),(24,36,28)]:
            loads=split_load(poly,field,freq,mic,outer,inner,angle)
            for n in ((48,64,96) if outer==18 else (96,)):
                mm=truncate(q,n);ports=[q['U'][w.rear,:n] for w in wires]
                Y=[];O=[];dryY=[];metrics=[];op=[]
                for f,(Z,H,rep) in zip(freq,loads):
                    y,o,s=response(mm,ports,wires,Z[:n,:n],H[:,:n],f)
                    dy,_,dr=response(mm,ports,wires,np.zeros((n,n)),np.zeros((2,n)),f)
                    Y.append(y);O.append(o);dryY.append(dy);metrics.append(s);op.append(rep)
                    assert dr['gate']
                row=dict(modes=n,outer=outer,inner=inner,angle=angle,dryRelative=relative(dryY,dry),
                    metrics=metrics,operatorGate=all(x['gate'] for x in op),rawOriginalGate=all(x['rawGate'] for x in op))
                row['gate']=all(x['gate'] for x in metrics) and row['operatorGate']
                cases.append(row);outputs.append((np.array(Y),np.array(O)))
                path.write_text(json.dumps(dict(cases=cases,complete=False),indent=2,allow_nan=False))
                print('G3_MODAL_STRING_CASE '+json.dumps(row),flush=True)
        for (x,u),(y,v) in zip(outputs,outputs[1:]):
            b=relative(x,y);d=relative(u,v);checks.append(dict(mobility=b,pressure=d,gate=max(b,d)<=.05))
        gate=ds['gate'] and cases[-1]['dryRelative']<=.05 and all(x['gate'] for x in checks[-2:]) and cases[-1]['gate']
        extra=dict(dryReference=ds,keys=keys,wireCount=len(wires),ports=labels,microphonesXYZ_m=mic.tolist())
    eigGate=q['massError']<=1e-5 and q['scaledEigenResidual']<=1e-8 and q['originalEigenResidual']<=1e-5
    summary=dict(case=a.case,cases=cases,convergence=checks,eigenGate=eigGate,eigenResidual=q['originalEigenResidual'],
        gate=gate and eigGate,integratedReady=False,radiationReady=False,**extra)
    path.write_text(json.dumps(dict(summary=summary,frequenciesHz=freq.tolist(),scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_MODAL_STRING_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'modal strings/radiation convergence'
if __name__=='__main__':main()

"""Common-space monopole reference, including cross radiation, 30–150 Hz."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from hybrid_cavity import build,response
from lid_exterior import load,pressure
from common_exterior import board_panel,eliminate
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));mic=np.asarray(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    m=build(poly,24,8,g['rimTopZ_m'],a.angle,field,6)
    panels=m['panels']+[board_panel(poly,field)]
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    freq=[30.,80.,150.];cavity=[response(m,f,mic) for f in freq]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'common_exterior.json'
    rows=[];outputs=[]
    for outer,inner,angular in [(12,22,24),(18,32,28),(24,42,36)]:
        ext=load(panels,freq,outer,inner,angular);vals=[];reps=[]
        for f,(Zc,Pc,cr),(Ze,er) in zip(freq,cavity,ext):
            total,pr,U,Q,r=eliminate(Zc,Pc,Ze,4)
            pe=pressure(panels,Q,far,f,outer)
            block=Ze.copy();block[:-4,-4:]=0;block[-4:,:-4]=0
            z0,p0,u0,q0,r0=eliminate(Zc,Pc,block,4)
            vals.append((total,pr,U,pe))
            reps.append(dict(frequencyHz=f,interior=cr,exterior=er,common=r,independent=r0,
                crossImpedanceEffect=relative(total,z0),crossFlowEffect=relative(U,u0),
                crossPressureEffect=relative(pr,p0)))
        row=dict(outer=outer,inner=inner,angular=angular,gate=all(all(v[k]['gate'] for k in ('interior','exterior','common','independent')) for v in reps),reports=reps)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_COMMON_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[[dict(frequencyHz=f,**{k:relative(x,y) for k,x,y in zip(('impedance','pressure','flow','exteriorPressure'),v,w)})
        for f,v,w in zip(freq,xs,ys)] for xs,ys in zip(outputs,outputs[1:])]
    gate=all(r['gate'] for r in rows) and all(max(q[k] for k in ('impedance','pressure','flow','exteriorPressure'))<=.05 for q in checks[-1])
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,apertureModes=36,boardFields=4,
        commonFreeSpaceMonopolesOnly=True,finiteRimNeumannReady=False,screenCorrectionIncluded=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_COMMON_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()

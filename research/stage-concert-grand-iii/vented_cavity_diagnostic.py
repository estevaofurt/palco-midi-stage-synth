"""Fixed flat aperture variants; independently refine cavity and exterior integrals."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from closed_cavity import assemble
from vented_cavity import aperture,exterior,response
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));c=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.array(c['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    mic=np.array(g['microphonesXYZ_m']);height=g['rimTopZ_m']
    def field(xy):
        x,y=(2*(xy-poly.min(0))/(poly.max(0)-poly.min(0))-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    freq=[30.,50.,80.,110.,150.];samples=[20+2j*np.pi*f for f in freq]+[2j*np.pi*f for f in freq]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'vented_cavity.json'
    summaries=[]
    for fraction in (.15,.4):
        cut=poly[:,0].max()-fraction*np.ptp(poly[:,0]);rows=[];outputs=[];m=None;last=None;ext={}
        for n,nz,outer,inner in [(12,4,12,20),(18,6,12,20),(24,8,12,20),(24,8,18,28)]:
            if last!=(n,nz):
                m=assemble(poly,n,nz,height,field);last=(n,nz)
            ap,A,C=aperture(m,poly,cut);Z=[];P=[];U=[];metrics=[]
            for s in samples:
                key=(s,outer,inner)
                if key not in ext:ext[key]=exterior(ap,A,s,m['rho'],m['c'],outer,inner)
                z,p,u,rep=response(m,C,s,mic,ext[key]);Z.append(z);P.append(p);U.append(u);metrics.append(rep)
            row=dict(n=n,nz=nz,outer=outer,inner=inner,areaM2=A,nodes=len(m['xyz']),
                powerRelative=max(x['powerRelative'] for x in metrics),reciprocity=max(x['reciprocity'] for x in metrics),
                pressureContinuity=max(x['pressureContinuity'] for x in metrics),minPassivity=min(x['passivityMinRelative'] for x in metrics),
                exteriorPowerTrace=[x['exteriorPowerTrace'] for x in metrics],gate=all(x['gate'] for x in metrics))
            rows.append(row);outputs.append((np.array(Z),np.array(P),np.array(U)))
            print('G3_VENT_CASE '+json.dumps(row),flush=True)
        checks=[]
        for (x,u,j),(y,v,k) in zip(outputs,outputs[1:]):
            z=relative(x,y);p=relative(u,v);flow=relative(j,k)
            checks.append(dict(impedance=z,pressure=p,flow=flow,gate=max(z,p,flow)<=.05))
        summaries.append(dict(widthFraction=fraction,cases=rows,convergence=checks,
            gate=all(q['gate'] for q in rows) and all(q['gate'] for q in checks[-2:])))
        path.write_text(json.dumps(dict(openings=summaries,complete=False),indent=2,allow_nan=False))
    summary=dict(openings=summaries,gate=all(q['gate'] for q in summaries),cabinetReady=False,openLidReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,frequenciesHz=freq,microphonesXYZ_m=mic.tolist(),scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_VENT_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'vent convergence'
if __name__=='__main__':main()

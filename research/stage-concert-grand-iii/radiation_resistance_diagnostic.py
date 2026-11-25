"""Geometry-based radiation proof using four prescribed velocity fields, NOT structural eigenmodes."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from ribbed_plate import quadrature
from radiation_resistance import angular,surface,pressure,far_amplitude,hemisphere
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def fields(xy,poly):
    # Uniform and three independent smooth test fields, not physical mode shapes.
    p=2*(xy-poly.min(0))/(poly.max(0)-poly.min(0))-1
    x,y=p.T
    return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
def rel(x,y):return float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30))
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));c=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.array(c['contourXY_m']);mic=np.array([q['xyzM'] for q in l['capture']]);rho=1.204;speed=343.;rows=[]
    for f in (80.,250.,500.,1000.):
        Y=[];P=[]
        for order,angle in ((12,32),(18,32),(24,32),(24,48)):
            xy,w=quadrature(poly,order);S=fields(xy,poly)
            assert abs(sum(w)-c['summary']['areaM2'])<1e-10
            Y.append(angular(xy,w,S,f,rho,speed,angle));P.append(pressure(xy,w,S,mic,f,rho,speed))
        direct=surface(xy,w,S,f,rho,speed);v=np.array([.3+.1j,-.2+.4j,.1-.1j,.2+.3j])
        d,weights=hemisphere(48);q=far_amplitude(xy,w,S,d,f,rho,speed)@v
        W=.5*float((v.conj()@Y[-1]@v).real);Wfar=float(weights@abs(q)**2)/(2*rho*speed)
        e=dict(surface12to18=rel(Y[0],Y[1]),surface18to24=rel(Y[1],Y[2]),angle32to48=rel(Y[2],Y[3]),
            kernel=rel(direct,Y[-1]),power=abs(W-Wfar)/max(Wfar,1e-30),pressure18to24=rel(P[1],P[2]))
        row=dict(frequencyHz=f,errors=e,minimumResistanceEigenvalue=float(min(np.linalg.eigvalsh(Y[-1]))),radiatedPowerW=W,
            resistance=Y[-1].tolist(),pressureReal=P[-1].real.tolist(),pressureImag=P[-1].imag.tolist())
        row['gate']=max(e['surface18to24'],e['angle32to48'],e['pressure18to24'])<=.05 and max(e['kernel'],e['power'])<=1e-8 and W>=0
        rows.append(row)
    summary=dict(cases=[{k:v for k,v in x.items() if k not in ('resistance','pressureReal','pressureImag')} for x in rows],
        gate=all(x['gate'] for x in rows),radiationReady=False,reactiveLoading=False,causalModel=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'radiation_resistance.json').write_text(json.dumps(dict(summary=summary,rows=rows,medium=dict(rhoKgM3=rho,speedMs=speed),microphonesXYZ_m=mic.tolist(),
        scaleSha256=hashlib.sha256(raw).hexdigest(),scope='one-sided infinite baffle, prescribed velocity fields, complex pressure and resistance only'),indent=2,allow_nan=False))
    print('G3_RADIATION_RESISTANCE_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'radiation quadrature'
if __name__=='__main__':main()

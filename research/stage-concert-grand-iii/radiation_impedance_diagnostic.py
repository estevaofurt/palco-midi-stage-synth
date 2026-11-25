"""Complex radiation impedance and causal observation proof, prescribed fields only."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from radiation_resistance_diagnostic import fields,rel
from radiation_resistance import surface,pressure
from radiation_impedance import impedance,audit,retarded_pressure
from ribbed_plate import quadrature
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));co=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.array(co['contourXY_m']);mic=np.array([q['xyzM'] for q in l['capture']]);rho=1.204;c=343.;rows=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'radiation_impedance.json'
    for f in (80.,250.,500.,1000.):
        w=2*np.pi*f;Z=[]
        for outer,inner in ((12,18),(18,24),(24,32)):
            Z.append(impedance(poly,fields,1j*w,rho,c,outer,inner))
        xy,weights=quadrature(poly,24);S=fields(xy,poly);R=surface(xy,weights,S,f,rho,c)
        e=dict(refinement12to18=rel(Z[0],Z[1]),refinement18to24=rel(Z[1],Z[2]),resistance=rel(Z[2].real,R))
        m=audit(Z[-1]);v=np.array([.3+.1j,-.2+.4j,.1-.1j,.2+.3j]);t=.02
        near=retarded_pressure(xy,weights,S,mic,t,lambda x:1j*w*np.exp(1j*w*x)[...,None]*v,rho,c)
        far=pressure(xy,weights,S,mic,f,rho,c)@v*np.exp(1j*w*t)
        e['observer']=rel(near,far)
        row=dict(frequencyHz=f,errors=e,metrics=m,impedanceReal=Z[-1].real.tolist(),impedanceImag=Z[-1].imag.tolist())
        # Finite quadrature reciprocity is measured, not forced by symmetrization.
        row['gate']=e['refinement18to24']<=.05 and e['resistance']<=1e-6 and e['observer']<=1e-10 and m['reciprocity']<=1e-3 and m['passivityMinRelative']>=-1e-8
        rows.append(row);print('G3_IMPEDANCE_CASE '+json.dumps({k:v for k,v in row.items() if not k.startswith('impedance')}),flush=True)
        path.write_text(json.dumps(dict(rows=rows,complete=False),indent=2,allow_nan=False))
    lap=[]
    for s in (100+2j*np.pi*80,500+2j*np.pi*500):
        z=impedance(poly,fields,s,rho,c,24,32);m=audit(z);lap.append(dict(realS=s.real,imagS=s.imag,**m,gate=m['reciprocity']<=1e-3 and m['passivityMinRelative']>=-1e-8))
    summary=dict(cases=[{k:v for k,v in q.items() if not k.startswith('impedance')} for q in rows],laplace=lap,gate=all(q['gate'] for q in rows+lap),
        radiationReady=False,timeDomainLoadReady=False)
    path.write_text(json.dumps(dict(summary=summary,rows=rows,microphonesXYZ_m=mic.tolist(),scaleSha256=hashlib.sha256(raw).hexdigest(),scope='infinite baffle, smooth prescribed fields, continuum causal kernel; no discrete time load'),indent=2,allow_nan=False))
    print('G3_IMPEDANCE_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'impedance convergence'
if __name__=='__main__':main()

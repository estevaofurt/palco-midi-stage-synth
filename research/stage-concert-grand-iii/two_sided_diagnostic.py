"""Separated-domain acoustic reference, not finite cabinet scattering."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from inclined_lid import build
from closed_cavity import response as closed_response
from aperture_modes import response
from lid_exterior import ports,load,pressure
from split_radiation import split_load,relative
from two_sided_radiation import combine,fixture
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    mic=np.asarray(g['microphonesXYZ_m']);lo=mic.copy();lo[:,2]=abs(g['rimBottomZ_m'])+.12
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,1.5]])
    def field(xy,unused=None):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    I=np.eye(4)
    # Mechanical test fixture only: no inferred piano masses, stiffness or damping.
    M=I;K=np.diag((2*np.pi*np.array([43.,69.,101.,137.]))**2);D=2*I
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'two_sided.json'
    freq=[30.,50.,80.,110.,150.];rows=[];outputs=[]
    for n,nz,outer,inner,ang in [(24,8,22,38,32),(30,10,28,48,40)]:
        m,C0,q=build(poly,n,nz,g['rimTopZ_m'],a.angle,field)
        lower=split_load(poly,field,freq,lo,outer,inner,ang)
        if a.angle>0:
            panels,C=ports(m,C0,q,21)
            upper=load(panels,freq,outer,inner,ang,m['rho'],m['c'])
        Z=[];P=[];L=[];E=[];reports=[]
        for i,f in enumerate(freq):
            zd,pd,ld=lower[i]
            if a.angle>0:
                ze,ext=upper[i];zu,pu,U,ur=response(m,C,2j*np.pi*f,mic,ze)
                pe=pressure(panels,U,far,f,outer,m['rho'],m['c'])
            else:
                zu,pu,ur=closed_response(m,2j*np.pi*f,mic)
                ext=dict(gate=True);pe=np.zeros((len(far),4),complex)
            # Upward board velocity positive; lower outward velocity negative.
            total,parts,cr=combine(zu,zd,I,-I)
            V,fr=fixture(M,K,D,total,parts,f)
            Z.append(total);P.append(pu);L.append(-pd);E.append(pe)
            reports.append(dict(frequencyHz=f,upper=ur,exterior=ext,lower=ld,combined=cr,fixture=fr,
                observerFinite=bool(np.isfinite(pu@V).all() and np.isfinite(-pd@V).all() and np.isfinite(pe@V).all())))
        row=dict(n=n,nz=nz,outer=outer,inner=inner,angleDeg=a.angle,ports=0 if a.angle==0 else C.shape[1],
            gate=all(all(v[key]['gate'] for key in ('upper','exterior','lower','combined','fixture')) and v['observerFinite'] for v in reports),
            reports=reports)
        rows.append(row);outputs.append(tuple(np.array(v) for v in (Z,P,L,E)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_TWO_SIDE_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    vals=[relative(x,y) for x,y in zip(*outputs)]
    convergence=dict(zip(['impedance','upperPressure','lowerPressure','exteriorPressure'],vals))
    gate=all(r['gate'] for r in rows) and max(vals)<=.05
    summary=dict(gate=gate,angleDeg=a.angle,convergence=convergence,independentDomainsOnly=True,finiteRimCrossCouplingReady=False,screenCorrectionIncluded=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_TWO_SIDE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()

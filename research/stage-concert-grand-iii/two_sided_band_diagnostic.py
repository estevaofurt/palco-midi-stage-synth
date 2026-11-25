"""150-300 Hz separated-domain reference, with independent modal and mesh checks.
No diffracting lid or finite-rim feedback. Diagnostic only.
"""
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
def compare(a,b):
    keys=('impedance','upperPressure','lowerPressure','exteriorPressure','netPanelFlow')
    return {k:max(relative(x,y) for x,y in zip(a[i],b[i])) if a[i].size else 0.
            for i,k in enumerate(keys)}
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
    I=np.eye(4);M=I;K=np.diag((2*np.pi*np.array([43.,69.,101.,137.]))**2);D=2*I
    freq=[150.,200.,250.,300.];rows=[];outputs=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'two_sided_band.json'
    configurations=[(30,10,24,42,32),(40,14,24,42,32),(40,14,30,52,40)]
    for n,nz,outer,inner,ang in configurations:
        m,C0,q=build(poly,n,nz,g['rimTopZ_m'],a.angle,field)
        lower=split_load(poly,field,freq,lo,outer,inner,ang)
        if a.angle>0:
            panels,C=ports(m,C0,q,21,canonical=True)
            upper=load(panels,freq,outer,inner,ang,m['rho'],m['c'])
        counts=[15,21] if a.angle>0 else [0]
        for count in counts:
            Z=[];P=[];L=[];E=[];F=[];reports=[]
            for i,f in enumerate(freq):
                zd,pd,ld=lower[i]
                if count:
                    ze,ext=upper[i]
                    ix=np.concatenate([np.arange(j*21,j*21+count) for j in range(len(panels))])
                    zu,pu,U,ur=response(m,C[:,ix],2j*np.pi*f,mic,ze[np.ix_(ix,ix)])
                    full=np.zeros((C.shape[1],U.shape[1]),complex);full[ix]=U
                    pe=pressure(panels,full,far,f,outer,m['rho'],m['c']);flow=full[::21]
                else:
                    zu,pu,ur=closed_response(m,2j*np.pi*f,mic)
                    ext=dict(gate=True);pe=np.zeros((len(far),4),complex);flow=np.zeros((0,4),complex)
                total,parts,cr=combine(zu,zd,I,-I)
                V,fr=fixture(M,K,D,total,parts,f)
                Z.append(total);P.append(pu);L.append(-pd);E.append(pe);F.append(flow)
                reports.append(dict(frequencyHz=f,upper=ur,exterior=ext,lower=ld,combined=cr,fixture=fr,
                    observerFinite=bool(np.isfinite(pu@V).all() and np.isfinite(-pd@V).all() and np.isfinite(pe@V).all())))
            row=dict(n=n,nz=nz,outer=outer,inner=inner,angular=ang,angleDeg=a.angle,modesPerPanel=count,
                gate=all(all(v[k]['gate'] for k in ('upper','exterior','lower','combined','fixture')) and v['observerFinite'] for v in reports),reports=reports)
            rows.append(row);outputs.append(tuple(np.array(v) for v in (Z,P,L,E,F)))
            path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
            print('G3_BAND_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    if a.angle>0:
        modal=[compare(outputs[i],outputs[i+1]) for i in (0,2,4)]
        mesh=compare(outputs[1],outputs[3]);quad=compare(outputs[3],outputs[5])
    else:
        modal=[];mesh=compare(outputs[0],outputs[1]);quad=compare(outputs[1],outputs[2])
    gate=all(r['gate'] for r in rows) and all(max(v.values())<=.05 for v in modal[-1:]+[mesh,quad])
    summary=dict(gate=gate,angleDeg=a.angle,modalConvergence=modal,meshConvergence=mesh,quadratureConvergence=quad,
        convergenceMetric='maximum across individual frequencies',canonicalPorts=True,independentDomainsOnly=True,
        finiteRimCrossCouplingReady=False,screenCorrectionIncluded=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BAND_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()

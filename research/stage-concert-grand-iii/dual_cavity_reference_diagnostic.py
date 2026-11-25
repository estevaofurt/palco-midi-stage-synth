"""Coupled upper/lower domains with common free-space monopole reference.
Not a finite-rim exterior solution. Fixed aperture bases; separate spatial
and exterior quadrature changes. No damping or shifts of acoustic poles.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from cabinet_geometry import geometry
from hybrid_cavity import build as upper_build,response as upper_response
from lower_prism import build as lower_build,response as lower_response
from recess_envelope import build as envelope
from bem_envelope import triangulate
from acoustic_port_bridge import compatible
from port_coordinates import transform
from lid_exterior import load,pressure
from dual_cavity_reference import couple
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
KEYS=('impedance','upperPressure','lowerPressure','exteriorPressure','flow')
def compare(freq,a,b):
    return [dict(frequencyHz=f,**{k:relative(x,y) for k,x,y in zip(KEYS,v,w)}) for f,v,w in zip(freq,a,b)]
def maximum(rows):
    return {k:max(r[k] for r in rows) for k in KEYS}
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    mic=np.asarray(g['microphonesXYZ_m']);h=-g['rimBottomZ_m'];_,center,_=properties(poly)
    lower_points=np.array([np.r_[center,-.25*h],np.r_[center,-.75*h]])
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    surf,ports,inside,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,6,field,10)
    t,labels,top=triangulate(surf,1);assert top['gate'] and abs(top['volume']-geo['volume'])<=1e-10
    na=sum(p.basis.count for p in ports[:-1]);nl=ports[-1].basis.count;nb=4
    freq=[30.,80.,150.,200.,250.,300.];rows=[];outputs=[];a.out.mkdir(parents=True,exist_ok=True);path=a.out/'dual_cavity_reference.json'
    def exterior(outer,inner,angular):
        result=[]
        for f,(Z,r) in zip(freq,load(ports,freq,outer,inner,angular)):
            assert r['gate'];P=pressure(ports,np.eye(len(Z)),far,f,outer)
            result.append((Z,P,r))
        return result
    def interior(n,nz,nlower):
        u=upper_build(poly,n,nz,g['rimTopZ_m'],a.angle,field,6);l=lower_build(poly,nlower,h,field,10)
        canonical=u['panels']+[l['mouth']]
        assert len(canonical)==len(ports) and all(compatible(x,y) for x,y in zip(ports,canonical))
        E,br=transform(ports,canonical);assert max(br.values())<=1e-8
        cases=[]
        for f in freq:
            Zu,Pu,ru=upper_response(u,f,mic);Zl,Pl,rl=lower_response(l,2j*np.pi*f,lower_points)
            assert ru['gate'] and rl['gate'];cases.append((Zu,Pu,Zl,Pl,ru,rl))
        return cases,E,br
    def evaluate(cases,E,br,ext,config):
        vals=[];reps=[]
        for f,(Zu,Pu,Zl,Pl,ru,rl),(Z,P,er) in zip(freq,cases,ext):
            Ze=E.T@Z@E;Pe=P@E
            total,pu,pl,pe,F,r=couple(Zu,Pu,Zl,Pl,Ze,Pe,nb,reference_kind='common-free-space-monopole')
            # Independently audit coordinate work and compare against an
            # explicitly uncoupled exterior (cross blocks omitted).
            work=relative(F.conj().T@Ze@F,(E@F).conj().T@Z@(E@F))
            independent=Ze.copy();independent[:na,na:]=0.;independent[na:,:na]=0.
            zi,pui,pli,pei,fi,ri=couple(Zu,Pu,Zl,Pl,independent,Pe,nb,reference_kind='common-free-space-monopole')
            vals.append((total,pu,pl,pe,F))
            reps.append(dict(frequencyHz=f,upper=ru,lower=rl,exterior=er,coupled=r,independent=ri,
                coordinateWorkRelative=work,crossImpedanceEffect=relative(total,zi),crossFlowEffect=relative(F,fi),
                crossExteriorPressureEffect=relative(pe,pei),gate=bool(r['gate'] and ri['gate'] and work<=1e-8)))
        row=dict(**config,coordinateBridge=br,reports=reps,gate=all(r['gate'] for r in reps))
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,geometry=geo,complete=False),indent=2,allow_nan=False))
        print('G3_DUAL_REFERENCE_CASE '+json.dumps(dict(**config,gate=row['gate'],maxCrossImpedanceEffect=max(r['crossImpedanceEffect'] for r in reps),maxCrossFlowEffect=max(r['crossFlowEffect'] for r in reps))),flush=True)
    ext=exterior(18,32,28)
    for n,nz,nlower in [(24,8,50),(30,10,60),(40,14,72)]:
        cases,E,br=interior(n,nz,nlower)
        evaluate(cases,E,br,ext,dict(upperN=n,upperNz=nz,lowerN=nlower,outer=18,inner=32,angular=28))
    # Same interior matrices and coordinates; only exterior quadrature changes.
    ext=exterior(24,42,36)
    evaluate(cases,E,br,ext,dict(upperN=40,upperNz=14,lowerN=72,outer=24,inner=42,angular=36))
    mesh=compare(freq,outputs[1],outputs[2]);quad=compare(freq,outputs[2],outputs[3])
    meshmax=maximum(mesh);quadmax=maximum(quad)
    gate=all(r['gate'] for r in rows) and max(meshmax.values())<=.05 and max(quadmax.values())<=.05
    summary=dict(gate=gate,angleDeg=a.angle,meshConvergence=meshmax,quadratureConvergence=quadmax,
        meshByFrequency=mesh,quadratureByFrequency=quad,upperApertureModes=na,lowerMouthModes=nl,boardFields=nb,
        commonFreeSpaceMonopolesOnly=True,apertureModeConvergenceIncluded=False,finiteRimNeumannReady=False,
        fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,geometry=geo,topology=top,
        frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_DUAL_REFERENCE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()

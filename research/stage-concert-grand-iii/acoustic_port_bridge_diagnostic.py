"""Validate reference coupling across actual envelope and cavity coordinates.
No BEM promotion; independent canonical common monopole reference.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from hybrid_cavity import build,response
from neumann_envelope import envelope,geometry_audit
from common_exterior import board_panel,eliminate
from lid_exterior import load,pressure
from acoustic_port_bridge import bridge,reference_couple
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
    surf,ports,center=envelope(poly,g['rimTopZ_m'],a.angle,6,field);geo=geometry_audit(surf,ports,center);assert geo['gate']
    board=board_panel(poly,field);canonical=m['panels']+[board]
    # Deliberately reorder the exterior aperture blocks to test matching.
    exterior=ports[:-1][::-1]+ports[-1:]
    E,br=bridge(m['panels'],exterior,board)
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    freq=[30.,80.,150.];rows=[];a.out.mkdir(parents=True,exist_ok=True);path=a.out/'acoustic_port_bridge.json'
    for outer,inner,angular in [(18,32,28),(24,42,36)]:
        ref=load(canonical,freq,outer,inner,angular);ext=load(exterior,freq,outer,inner,angular);reps=[]
        for f,(Zr,rr),(Ze,er) in zip(freq,ref,ext):
            Zc,Pc,cr=response(m,f,mic);assert cr['gate'] and rr['gate'] and er['gate']
            I=np.eye(len(Ze));Pe=pressure(exterior,I,far,f,outer)
            total,pi,pe,U,Q,rep=reference_couple(Zc,Pc,Ze,Pe,E,4,reference_kind='common-free-space-monopole')
            z0,p0,u0,q0,r0=eliminate(Zc,Pc,Zr,4);pFar0=pressure(canonical,q0,far,f,outer)
            diff=dict(impedance=relative(total,z0),interiorPressure=relative(pi,p0),exteriorPressure=relative(pe,pFar0),flow=relative(U,u0),exteriorLoad=relative(E.T@Ze@E,Zr))
            reps.append(dict(frequencyHz=f,bridge=br,coupled=rep,reference=r0,coordinateDifference=diff,
                gate=bool(rep['gate'] and r0['gate'] and max(diff.values())<=.01)))
        rows.append(dict(outer=outer,inner=inner,angular=angular,reports=reps,gate=all(r['gate'] for r in reps)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_PORT_BRIDGE_CASE '+json.dumps(dict(outer=outer,gate=rows[-1]['gate'],maxCoordinateDifference=max(max(r['coordinateDifference'].values()) for r in reps))),flush=True)
    gate=rows[-1]['gate'];summary=dict(gate=gate,angleDeg=a.angle,referenceOnly=True,
        finiteRimNeumannReady=False,coupledBEMReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_PORT_BRIDGE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()

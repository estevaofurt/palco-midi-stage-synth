"""G3.06p: independent cubic flux truncation and integration refinement."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from inclined_lid import build
from lid_exterior import ports,load,pressure
from aperture_modes import response
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.array(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));mic=np.array(g['microphonesXYZ_m'])
    # Independent far observers, not replacements for the unchanged interior mics.
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,1.5]])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'lid_exterior_cubic.json'
    freq=[30.,50.,80.,110.,150.];rows=[];outputs=[];cache={};key=None
    for n,nz,count,outer,inner,ang in [(24,8,6,16,28,24),(24,8,10,16,28,24),(24,8,10,22,38,32),(30,10,10,22,38,32),(30,10,10,28,48,40)]:
        if key!=(n,nz):
            m,C0,q=build(poly,n,nz,g['rimTopZ_m'],a.angle,field);panels,C=ports(m,C0,q,10);key=(n,nz)
        lk=(outer,inner,ang)
        if lk not in cache:cache[lk]=load(panels,freq,outer,inner,ang,m['rho'],m['c'])
        ix=np.concatenate([np.arange(i*10,i*10+count) for i in range(len(panels))]);Y=[];P=[];F=[];E=[];O=[];reports=[]
        for f,(Z,rep) in zip(freq,cache[lk]):
            z,p,u,met=response(m,C[:,ix],2j*np.pi*f,mic,Z[np.ix_(ix,ix)])
            full=np.zeros((C.shape[1],u.shape[1]),complex);full[ix]=u
            Y.append(z);P.append(p);F.append(full[::10]);E.append(pressure(panels,full,far,f,outer,m['rho'],m['c']));O.append(Z)
            reports.append(dict(operator=rep,response=met))
        row=dict(n=n,nz=nz,modesPerPanel=count,ports=len(ix),outer=outer,inner=inner,angular=ang,
            operatorGate=all(v['operator']['gate'] for v in reports),responseGate=all(v['response']['gate'] for v in reports),
            maxReactiveAsymmetry=max(v['operator']['reactiveAsymmetry'] for v in reports),reports=reports)
        rows.append(row);outputs.append(tuple(np.array(x) for x in (Y,P,F,E,O)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_CUBIC_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[]
    for x,y in zip(outputs,outputs[1:]):
        v=[relative(i,j) for i,j in zip(x,y)]
        checks.append(dict(zip(['impedance','interiorPressure','netPanelFlow','exteriorPressure','operator'],v),gate=max(v)<=.05))
    summary=dict(angleDeg=a.angle,convergence=checks,gate=all(q['responseGate'] for q in rows) and rows[-1]['operatorGate'] and all(v['gate'] for v in checks),
        modalTruncationGate=checks[0]['gate'],freeSpaceReferenceOnly=True,exteriorDiffractionReady=False,openLidReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,farObserversXYZ=far.tolist(),scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_CUBIC_GATE '+json.dumps(summary),flush=True);assert summary['gate']
if __name__=='__main__':main()

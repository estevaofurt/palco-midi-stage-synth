"""Refinement of flux-mode truncation, cavity mesh, and exterior quadrature."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from closed_cavity import assemble
from aperture_modes import aperture_modes,response,exterior
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--fraction',type=float,choices=[.15,.4],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));c=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.array(c['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    mic=np.array(g['microphonesXYZ_m']);height=g['rimTopZ_m']
    def field(xy):
        x,y=(2*(xy-poly.min(0))/(poly.max(0)-poly.min(0))-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    cut=poly[:,0].max()-a.fraction*np.ptp(poly[:,0]);freq=[30.,50.,80.,110.,150.]
    rows=[];outputs=[];cache=None;key=None;loads={}
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'aperture_modes.json'
    for n,nz,count,outer,inner,angle in [(24,8,1,24,36,24),(24,8,3,24,36,24),(24,8,6,24,36,24),(24,8,10,24,36,24),(30,10,10,24,36,24),(30,10,10,30,44,32)]:
        if key!=(n,nz):
            m=assemble(poly,n,nz,height,field);ap,b,C=aperture_modes(m,poly,cut,10);key=(n,nz)
        k=(outer,inner,angle)
        if k not in loads:loads[k]=exterior(ap,b,freq,outer,inner,angle,m['rho'],m['c'])
        Y=[];P=[];F=[];reports=[]
        for f,(Z,rep) in zip(freq,loads[k]):
            y,p,u,met=response(m,C[:,:count],2j*np.pi*f,mic,Z[:count,:count])
            Y.append(y);P.append(p);F.append(u[0]);reports.append(dict(operator=rep,response=met))
        row=dict(n=n,nz=nz,fluxModes=count,outer=outer,inner=inner,angle=angle,areaM2=b.area,
            operatorGate=all(x['operator']['gate'] for x in reports),rawOriginalGate=all(x['operator']['rawGate'] for x in reports),
            responseGate=all(x['response']['gate'] for x in reports),reports=reports)
        row['gate']=row['operatorGate'] and row['responseGate'];rows.append(row);outputs.append((np.array(Y),np.array(P),np.array(F)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_APERTURE_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[]
    for (x,u,j),(y,v,k) in zip(outputs,outputs[1:]):
        e=relative(x,y);p=relative(u,v);flow=relative(j,k)
        checks.append(dict(impedance=e,pressure=p,netVolumeFlow=flow,gate=max(e,p,flow)<=.05))
    summary=dict(widthFraction=a.fraction,cases=[{k:v for k,v in row.items() if k!='reports'} for row in rows],convergence=checks,
        gate=all(x['responseGate'] for x in rows) and rows[-1]['operatorGate'] and all(q['gate'] for q in checks[-3:]),
        cabinetReady=False,openLidReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_APERTURE_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'aperture mode convergence'
if __name__=='__main__':main()

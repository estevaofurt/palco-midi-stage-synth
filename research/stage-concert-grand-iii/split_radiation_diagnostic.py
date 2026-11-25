"""Nested modal refinement and independent radiation operator convergence.
Keep all original results; never declare the earlier raw quadrature passed.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from structural_response import response as direct_response
from polygon_radiation import modes,SurfaceModes,response
from split_radiation import split_load,relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def truncate(q,n):
    return dict(M=q['M'][:n,:n],K=q['K'][:n,:n],D=q['D'][:n,:n],P=q['P'][:n])
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.array(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    mic=np.array([q['xyzM'] for q in l['capture']]);freq=np.array([30.,50.,80.,110.,150.])
    m=assemble(poly,c['ribs'],mat['plate'],rib,30,14,False)
    z=structure(m,centers,read('bridge_hypothesis.json'),mat,read('rim_structure_hypothesis.json'),2,8,14,True)
    M=z['M'];K=z['K']+z['Jrim']+z['Jbridge'];D=z['D'];P=z['P'][:,[0,2,4,5]]
    dry,ds,_=direct_response(M,K,D,P,freq,np.ones(4));q=modes(M,K,D,P,64)
    eigGate=q['massError']<=1e-5 and q['scaledEigenResidual']<=1e-8 and q['originalEigenResidual']<=1e-5
    dryRows=[]
    for n in (12,24,32,48,64):
        mm=truncate(q,n);Y=[response(mm,np.zeros((n,n)),np.zeros((2,n)),f)[0] for f in freq]
        dryRows.append(dict(modes=n,highestModeHz=float(q['Hz'][n-1]),relative=relative(Y,dry)))
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'split_radiation.json'
    path.write_text(json.dumps(dict(dry=dryRows,dryReference=ds,eigenGate=eigGate,complete=False),indent=2))
    print('G3_SPLIT_DRY '+json.dumps(dryRows),flush=True)
    field=SurfaceModes(m,q['U'][:z['plateDofs']]);rows=[];outputs=[]
    # Same 64-dimensional integration, nested submatrices eliminate inconsistent
    # eigenvector sign/basis effects in comparisons. Coarse quadrature remains diagnostic.
    for outer,inner,angle in [(18,28,20),(24,36,20),(24,36,28)]:
        loads=split_load(poly,field,freq,mic,outer,inner,angle)
        for n in ((32,48,64) if outer==18 else (64,)):
            mm=truncate(q,n);Y=[];Obs=[];reports=[]
            for f,(Z,H,rep) in zip(freq,loads):
                # Audit full 64-mode operators even for nested subsets.
                y,o,s=response(mm,Z[:n,:n],H[:,:n],f)
                Y.append(y);Obs.append(o);reports.append(dict(operator=rep,coupled=s))
            op=[x['operator'] for x in reports];cp=[x['coupled'] for x in reports]
            row=dict(modes=n,outer=outer,inner=inner,angle=angle,rawGate=all(x['rawGate'] for x in op),
                rawMinPassivity=min(x['rawMinPassivity'] for x in op),rawResistanceRelative=max(x['rawResistanceRelative'] for x in op),
                reactiveAsymmetry=max(x['reactiveAsymmetry'] for x in op),gramVsSurface=max(x['gramVsSurface'] for x in op),
                splitVsRaw=max(x['splitVsRaw'] for x in op),reciprocity=max(x['reciprocity'] for x in cp),powerRelative=max(x['powerRelative'] for x in cp),
                passivityMinRelative=min(x['passivityMinRelative'] for x in cp),airPowerFraction=[x['airPowerFraction'] for x in cp])
            row['gate']=all(x['gate'] for x in op) and row['reciprocity']<=1e-8 and row['powerRelative']<=1e-6 and row['passivityMinRelative']>=-1e-8
            rows.append(row);outputs.append((np.array(Y),np.array(Obs)))
            print('G3_SPLIT_CASE '+json.dumps(row),flush=True)
            path.write_text(json.dumps(dict(dry=dryRows,cases=rows,complete=False),indent=2,allow_nan=False))
    checks=[]
    for (x,u),(y,v) in zip(outputs,outputs[1:]):
        a=relative(x,y);b=relative(u,v);checks.append(dict(mobility=a,pressure=b,gate=max(a,b)<=.05))
    summary=dict(dry=dryRows,dryReferenceGate=ds['gate'],eigenGate=eigGate,originalEigenResidual=q['originalEigenResidual'],
      cases=rows,convergence=checks,gate=ds['gate'] and eigGate and dryRows[-1]['relative']<=.05 and all(x['gate'] for x in checks[-3:]) and rows[-1]['gate'],
      rawOriginalGate=rows[-1]['rawGate'],radiationReady=False,integratedReady=False)
    path.write_text(json.dumps(dict(summary=summary,frequenciesHz=freq.tolist(),microphonesXYZ_m=mic.tolist(),scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_SPLIT_RADIATION_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'split radiation convergence'
if __name__=='__main__':main()

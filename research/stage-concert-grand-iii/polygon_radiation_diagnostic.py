"""Low-band soundboard radiation using the actual assembled candidate structure.
Separate modal and spatial convergence; no time-domain fit and no strings.
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
from polygon_radiation import modes,SurfaceModes,load,response
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def rel(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-30))
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.array(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    mic=np.array([q['xyzM'] for q in l['capture']])
    freq=np.array([30.,50.,80.,110.,150.]);rows=[];Y=[];Obs=[];old=None
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'polygon_radiation.json'
    for cells,count,outer,inner in [(24,12,12,18),(30,12,12,18),(30,24,12,18),(30,24,18,28)]:
        if old!=cells:
            m=assemble(poly,c['ribs'],mat['plate'],rib,cells,14,False)
            z=structure(m,centers,read('bridge_hypothesis.json'),mat,read('rim_structure_hypothesis.json'),2,8,14,True)
            M=z['M'];K=z['K']+z['Jrim']+z['Jbridge'];D=z['D'];P=z['P'][:,[0,2,4,5]]
            dry,ds,_=direct_response(M,K,D,P,freq,np.ones(4))
            old=cells
        q=modes(M,K,D,P,count)
        field=SurfaceModes(m,q['U'][:z['plateDofs']])
        yy=[];oo=[];dryReduced=[];rr=[];mm=[]
        for f in freq:
            Z,H,audit=load(poly,field,f,mic,outer,inner);rr.append(audit)
            y,o,metrics=response(q,Z,H,f);yy.append(y);oo.append(o);mm.append(metrics)
            d,_,_=response(q,np.zeros_like(Z),H,f);dryReduced.append(d)
        Y.append(np.array(yy));Obs.append(np.array(oo))
        row=dict(cells=cells,modeCount=count,outer=outer,inner=inner,highestModeHz=float(q['Hz'][-1]),
          first8Hz=q['Hz'][:8].tolist(),massError=q['massError'],scaledEigenResidual=q['scaledEigenResidual'],originalEigenResidual=q['originalEigenResidual'],
          dryReferenceGate=ds['gate'],dryReducedRelative=rel(np.array(dryReduced),dry),
          rawReciprocity=max(x['reciprocity'] for x in rr),rawMinPassivity=min(x['passivityMinRelative'] for x in rr),
          resistanceRelative=max(x['resistanceRelative'] for x in rr),projectionRelative=max(x['projectionRelative'] for x in rr),
          powerRelative=max(x['powerRelative'] for x in mm),reciprocity=max(x['reciprocity'] for x in mm),
          passivityMinRelative=min(x['passivityMinRelative'] for x in mm),
          airPowerFraction=[x['airPowerFraction'] for x in mm])
        row['gate']=ds['gate'] and q['massError']<=1e-5 and q['scaledEigenResidual']<=1e-8 and q['originalEigenResidual']<=1e-5 and row['rawReciprocity']<=1e-3 and row['rawMinPassivity']>=-1e-8 and row['resistanceRelative']<=.01 and row['projectionRelative']<=.01 and row['reciprocity']<=1e-8 and row['powerRelative']<=1e-6 and row['passivityMinRelative']>=-1e-8
        rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_POLYGON_RADIATION_CASE '+json.dumps(row),flush=True)
    checks=[dict(mobility=rel(x,y),pressure=rel(u,v)) for x,y,u,v in zip(Y,Y[1:],Obs,Obs[1:])]
    for d in checks:d['gate']=max(d['mobility'],d['pressure'])<=.05
    summary=dict(cases=rows,convergence=checks,gate=all(q['gate'] for q in rows) and all(q['gate'] for q in checks) and rows[-1]['dryReducedRelative']<=.05,
        radiationReady=False,integratedReady=False)
    path.write_text(json.dumps(dict(summary=summary,frequenciesHz=freq.tolist(),microphonesXYZ_m=mic.tolist(),
      mobilityReal=Y[-1].real.tolist(),mobilityImag=Y[-1].imag.tolist(),pressureReal=Obs[-1].real.tolist(),pressureImag=Obs[-1].imag.tolist(),
      scaleSha256=hashlib.sha256(raw).hexdigest(),scope='candidate polygon with ribs rim and bridges, low-mode frequency-domain projection, no strings'),indent=2,allow_nan=False))
    print('G3_POLYGON_RADIATION_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'polygon radiation accuracy'
if __name__=='__main__':main()

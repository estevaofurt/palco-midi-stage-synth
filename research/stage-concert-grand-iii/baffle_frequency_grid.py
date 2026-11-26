"""G3.12d: fixed 18-frequency enriched ideal-baffle reference.
No fitting. Development and independent validation arrays stored together
with an explicit frozen split. No cabinet or time-domain certification."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from enriched_baffle import load_source,samples,resistance
from surface_reactive_fft import cell_integrals,reactive,wet_response
from radiation_resistance import pressure
from acoustic_matrix_archive import read_npz
from dry_structural_modal import read
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from spline_plate import assemble
from polygon_radiation import SurfaceModes
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

TRAIN=[30.,45.,80.,95.,135.,150.,185.,200.,235.,250.,285.,300.]
VALID=[65.,115.,160.,215.,260.,295.]
PREVIOUS=[30.,150.,300.]
FREQ=sorted(TRAIN+VALID)

def check_split():
    if len(FREQ)!=18 or len(set(FREQ))!=18 or not set(PREVIOUS)<=set(TRAIN) or set(TRAIN)&set(VALID):
        raise ValueError('invalid frozen split')

def require_previous(root,sha):
    raw=(root/'surface_reactive_fft.json').read_bytes();d=json.loads(raw);s=d['summary']
    required=dict(gate=True,diagnosticOnly=True,physicalHypothesis=True,fields=72,oneSidedIdealBaffle=True,
        reactanceIncluded=True,cellAverageApproximation=True,gridSizes=[60,120,240],calibratedParameters=False,
        acousticFitAccepted=False,timeDomainReady=False,radiationReady=False)
    if any(s.get(k)!=v for k,v in required.items()) or d['sourceFrozenSha256']!=sha or d['frequenciesHz']!=PREVIOUS:
        raise ValueError('incompatible reactive source')
    if s['maximumFineError']>.005 or s['kernelOrderRelative']>1e-6 or s['maximumAreaError']>1e-9:
        raise ValueError('invalid prior convergence')
    if [v['frequencyHz'] for v in d['cases']]!=PREVIOUS or not all(v['gate'] is True for v in d['cases']):
        raise ValueError('incomplete prior evidence')
    data=read_npz(root,d['archive'],dict(impedance=(3,72,72),pressure=(3,2,72),mobility=(3,4,4),observation=(3,2,4)),PREVIOUS)
    return data,hashlib.sha256(raw).hexdigest()

def compute(z,field,plate,poly,mic,freq):
    x0,w0,S0=samples(plate,field,6);x1,w1,S1=samples(plate,field,8)
    gram=relative(S1.T@(w1[:,None]*S1),np.eye(72))
    if gram>1e-7:raise ValueError('surface reconstruction')
    grids={}
    for n in (60,120,240):
        B,dx,dy,area=cell_integrals(poly,field,n)
        if abs(area-plate['areaM2'])/plate['areaM2']>1e-9:raise ValueError('grid area mismatch')
        grids[n]=(B,dx,dy)
    rows=[];ZZ=[];HH=[];YY=[];OO=[]
    A=z['fieldMap']
    for f in freq:
        R0,r0=resistance(x0,w0,S0,f,12)
        R1,r1=resistance(x1,w1,S1,f,12)
        R,r2=resistance(x1,w1,S1,f,16)
        H0=pressure(x0,w0,S0,mic,f,1.204,343.)
        H=pressure(x1,w1,S1,mic,f,1.204,343.)
        X0,X1,X2=[reactive(*grids[n],f,8) for n in (60,120,240)]
        X12=reactive(*grids[240],f,12)
        spatial=relative(R0,R1);angular=relative(R1,R);obs=relative(H0,H)
        coarse=relative(X0,X1);fine=relative(X1,X2);kernel=relative(X12,X2)
        reciprocity=max(relative(X,X.T) for X in (X0,X1,X2,X12))
        Z=R+1j*(X2+X2.T)/2
        Y,O,audit=wet_response(z['stiffness'],z['damping'],z['ports'],A,Z,H,f)
        gate=bool(max(spatial,angular,obs,kernel)<=1e-6 and fine<=.005 and fine<coarse and reciprocity<=1e-10
            and all(max(r['imaginaryGramRelative'],r['reciprocity'])<=1e-8 and r['passivityMinRelative']>=-1e-10 for r in (r0,r1,r2))
            and max(audit['powerRelative'],audit['reciprocity'])<=1e-8 and audit['passivityMinRelative']>=-1e-8)
        row=dict(frequencyHz=f,role='training' if f in TRAIN else 'validation',
            resistanceSpatialRelative=spatial,resistanceAngularRelative=angular,pressureRelative=obs,
            reactiveCoarseRelative=coarse,reactiveFineRelative=fine,kernelRelative=kernel,reactiveReciprocity=reciprocity,
            resistanceAudit=r2,wetAudit=audit,gate=gate)
        rows.append(row);ZZ.append(Z);HH.append(H);YY.append(Y);OO.append(O)
        print('G3_BAFFLE_GRID_CASE '+json.dumps(row,allow_nan=False),flush=True)
    return rows,dict(impedance=np.stack(ZZ),pressure=np.stack(HH),mobility=np.stack(YY),observation=np.stack(OO)),gram

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','previous','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--role',choices=['training','validation'],required=True);a=p.parse_args()
    check_split();z,sha=load_source(a.source,a.scale);old,prevsha=require_previous(a.previous,sha)
    sc=json.loads(a.scale.read_bytes());l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    q=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.asarray(q['contourXY_m']);plate=assemble(poly,q['ribs'],mat['plate'],rib,30,14,False)
    field=SurfaceModes(plate,z['physicalLift'][:plate['rank']]@z['fieldVectors']/np.sqrt(z['fieldEigenvalues'])[None,:])
    center=poly.mean(0);mic=np.array([[center[0],center[1],.5],[center[0]+.25,center[1],1.5]])
    freq=TRAIN if a.role=='training' else VALID
    rows,data,gram=compute(z,field,plate,poly,mic,freq)
    replay=[]
    for i,f in enumerate(freq):
        if f in PREVIOUS:
            j=PREVIOUS.index(f);e={k:relative(v[i],old[k][j]) for k,v in data.items()}
            replay.append(dict(frequencyHz=f,errors=e,gate=max(e.values())<=1e-8))
    gate=all(v['gate'] for v in rows+replay)
    a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'baffle_grid_'+a.role,frequencies=freq,**data)
    summary=dict(gate=gate,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,fields=72,
        oneSidedIdealBaffle=True,role=a.role,pointCount=len(freq),surfaceGramRelative=gram,
        maximumReactiveError=max(v['reactiveFineRelative'] for v in rows),
        maximumKernelError=max(v['kernelRelative'] for v in rows),maximumPressureError=max(v['pressureRelative'] for v in rows),
        fitNotPerformed=True,acousticFitAccepted=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'baffle_grid.json').write_text(json.dumps(dict(summary=summary,cases=rows,replay=replay,archive=entry,
        sourceFrozenSha256=sha,previousManifestSha256=prevsha,frequenciesHz=freq,trainingHz=TRAIN,validationHz=VALID,
        microphonesXYZ_m=mic.tolist()),indent=2,allow_nan=False))
    print('G3_BAFFLE_GRID_GATE '+json.dumps(summary),flush=True)
    if not gate:raise ValueError('enriched frequency grid not approved')
if __name__=='__main__':main()

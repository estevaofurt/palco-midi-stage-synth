"""G3.12y: co-coordinate 80-mode wire/ideal-baffle harmonic reference.
Full complex radiation on the locally rebuilt surface, not the old 72 fields.
No causal fit or calibrated acoustic output."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import solve
from wire_physical_midpoint import CoupledWire,load
from structural_region_decay import rebuild
from hybrid_temporal_surface import surface_gram,surface_basis
from polygon_radiation import SurfaceModes
from enriched_baffle import samples,resistance
from surface_reactive_fft import cell_integrals,reactive
from radiation_resistance import pressure
from modal_string_radiation import response
from physical_unison_decay import detune
from dual_cavity_spatial_diagnostic import save_matrices
from split_radiation import relative

FREQ=[30.,150.,250.,261.4,261.63,261.86,300.]
CONFIGS=[(0.,1.),(1.,1.),(0.,.25),(1.,.25),(1.,.1)]

def dense_response(a,Z,H,f):
    M,K,D,P=a.matrices();n=a.n;w=2*np.pi*f
    drag=D.astype(complex);drag[:n,:n]+=Z
    Q=np.zeros((len(M),len(M)));Q[:n,:n]=Z.real
    s=1/np.sqrt(np.diag(M));G=K-w*w*M+1j*w*drag
    x=s[:,None]*solve(G*(s[:,None]*s[None,:]),s[:,None]*P)
    v=1j*w*x;Y=P.T@v;O=H@v[:n]
    power=(Y+Y.conj().T)/2
    dry=v.conj().T@D@v;air=v.conj().T@Q@v
    i=2;den=max(float(power[i,i].real),1e-30)
    audit=dict(powerRelative=relative(power,dry+air),reciprocity=relative(Y,Y.T),
        residual=relative(G@x,P),passivityMinRelative=float(np.linalg.eigvalsh(power).min()/max(np.linalg.norm(power),1e-30)),
        c4AirFraction=float(air[i,i].real/den),c4DryFraction=float(dry[i,i].real/den))
    audit['gate']=bool(max(audit['powerRelative'],audit['reciprocity'])<=1e-8 and audit['residual']<=1e-5
        and audit['passivityMinRelative']>=-1e-8 and min(audit['c4AirFraction'],audit['c4DryFraction'])>=-1e-10)
    return Y,O,audit

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','surface','regions','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale)
    raw=(a.regions/'structural_region_decay.json').read_bytes();d=json.loads(raw)
    if d['sourceFrozenSha256']!=sha or any(d['summary'].get(k)!=v for k,v in dict(gate=True,cases=28,localBasisRebuilt=True,acousticLoadIncluded=False).items()):
        raise ValueError('unapproved regional source')
    local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    plate,poly=local['plate'],local['poly']
    base=SurfaceModes(plate,local['lift'])
    H0,area0=surface_gram(plate['basis'],base,8,80);H,area=surface_gram(plate['basis'],base,12,80)
    ev,W=surface_basis(H);B=np.sqrt(ev)[:,None]*W.T
    gramError=relative(H0,H);mapError=relative(B.T@B,H)
    areaError=max(abs(area-plate['areaM2']),abs(area0-plate['areaM2']))/plate['areaM2']
    if max(gramError,mapError)>1e-8 or areaError>1e-10:raise ValueError('local surface map')
    field=SurfaceModes(plate,local['lift']@W/np.sqrt(ev)[None,:])
    x0,w0,S0=samples(plate,field,6);x1,w1,S1=samples(plate,field,8)
    normalizedGram=relative(S1.T@(w1[:,None]*S1),np.eye(len(ev)))
    if normalizedGram>1e-7:raise ValueError('orthonormal surface fields')
    grids={}
    for n in (120,240):
        C,dx,dy,ar=cell_integrals(poly,field,n)
        if abs(ar-plate['areaM2'])/plate['areaM2']>1e-9:raise ValueError('grid area')
        grids[n]=(C,dx,dy)
    center=poly.mean(0);mic=np.array([[*center,.5],[center[0]+.25,center[1],1.5]])
    Zs=[];Hs=[];kernels=[]
    for f in FREQ:
        R0,r0=resistance(x0,w0,S0,f,12);R1,r1=resistance(x1,w1,S1,f,12);R,r2=resistance(x1,w1,S1,f,16)
        X0=reactive(*grids[120],f,8);X=reactive(*grids[240],f,8);X12=reactive(*grids[240],f,12)
        H0=pressure(x0,w0,S0,mic,f,1.204,343.);H=pressure(x1,w1,S1,mic,f,1.204,343.)
        row=dict(frequencyHz=f,resistanceSpatial=relative(R0,R1),resistanceAngular=relative(R1,R),
            reactiveGrid=relative(X0,X),reactiveKernel=relative(X,X12),pressure=relative(H0,H),
            reciprocity=max(relative(X,X.T),relative(R,R.T)),passivityMin=min(v['passivityMinRelative'] for v in (r0,r1,r2)))
        row['gate']=bool(max(row[t] for t in ('resistanceSpatial','resistanceAngular','reactiveKernel','pressure'))<=1e-6
            and row['reactiveGrid']<=.005 and row['reciprocity']<=1e-10 and row['passivityMin']>=-1e-10)
        kernels.append(row);Zs.append(R+1j*(X+X.T)/2);Hs.append(H)
        print('G3_WIRE_BAFFLE_KERNEL '+json.dumps(row,allow_nan=False),flush=True)
    rows={t['key']:t for t in json.loads(a.scale.read_text())['rows']}
    cases=[];Yall=[];Oall=[]
    for spread,factor in CONFIGS:
        ww,tuning=detune(wires,rows,spread)
        md=dict(M=np.eye(80),K=np.diag(k),D=D*factor,P=P)
        reduced=CoupledWire(k,D*factor,P,A,ww,48000,32)
        Ys=[];Os=[]
        for f,Z,H in zip(FREQ,Zs,Hs):
            zz=B.T@Z@B;hh=H@B
            Y,O,wet=response(md,A,ww,zz,hh,f)
            Ydry,_,dry=response(md,A,ww,np.zeros_like(zz),hh,f)
            Y32,O32,audit=dense_response(reduced,zz,hh,f)
            row=dict(spreadCents=spread,structureFactor=factor,frequencyHz=f,
                wet=wet,dry=dry,reduced32=audit,reducedMobilityRelative=relative(Y32,Y),reducedPressureRelative=relative(O32,O),
                wetDryMobilityRelative=relative(Y,Ydry),c4PressurePaPerN=np.abs(O[:,2]).tolist())
            row['gate']=bool(wet['gate'] and dry['gate'] and audit['gate'])
            cases.append(row);Ys.append(Y);Os.append(O)
            print('G3_WIRE_BAFFLE_CASE '+json.dumps(row,allow_nan=False),flush=True)
        Yall.append(Ys);Oall.append(Os)
    summary=dict(gate=all(t['gate'] for t in kernels+cases),diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,
        structureRank=80,fields=len(ev),wires=10,frequencyPoints=len(FREQ),cases=len(cases),
        oneSidedIdealBaffle=True,coCoordinateSurface=True,oldAcousticOperatorsCompatible=False,
        surfaceGramRelative=gramError,surfaceMapRelative=mapError,normalizedGramRelative=normalizedGram,
        maximumReactiveGrid=max(v['reactiveGrid'] for v in kernels),
        maximumReducedMobility=max(v['reducedMobilityRelative'] for v in cases),
        maximumReducedPressure=max(v['reducedPressureRelative'] for v in cases),
        reduced32Gate=bool(max(max(v['reducedMobilityRelative'],v['reducedPressureRelative']) for v in cases)<=.05),
        acousticLoadHarmonicOnly=True,physicalAcousticFitAccepted=False,causalPressureObserverIncluded=False,
        audibleSustainMeasured=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'wire_baffle_reference',frequencies=FREQ,stiffness=k,damping=D,ports=P,wirePorts=A,
        physicalLift=lift,regionalDamping=G,fieldMap=B,fieldEigenvalues=ev,fieldVectors=W,
        impedance=np.stack(Zs),pressure=np.stack(Hs),mobility=np.asarray(Yall),observation=np.asarray(Oall))
    (a.out/'wire_baffle_reference.json').write_text(json.dumps(dict(summary=summary,kernels=kernels,cases=cases,
        frequenciesHz=FREQ,configurations=CONFIGS,microphonesXYZ_m=mic.tolist(),archive=entry,sourceFrozenSha256=sha,
        regionManifestSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_WIRE_BAFFLE_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('wire baffle harmonic proof failed')
if __name__=='__main__':main()

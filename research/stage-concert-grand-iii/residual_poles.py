"""G3.13j: identify physical modes underlying reported residual tones.
No calibration or retuning. Continuous mechanical poles mapped through
the actual midpoint integrator, energy/loss attribution in mass basis.
Frequency matches are candidates, not proof of excitation."""
import argparse,copy,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import eigh,eig
from wire_physical_midpoint import load,CoupledWire
from structural_passive_fit import read_reference
from dry_pressure_render import pressure_source
from physical_unison_decay import detune
from physical_pedal_repeat import damper_ports,PointDense
from causal_pressure_observer import transfer
from split_radiation import relative

TARGETS=[791.,1719.,1838.,1957.,2315.,2897.]
KEYS=[45,48,60,64]
def pole_data(M,K,D,rate):
    lam,U=eigh(K,M);n=len(lam)
    if min(lam)<=0:raise ValueError('stiffness')
    w=np.sqrt(lam);G=U.T@D@U
    A=np.block([[np.zeros((n,n)),np.diag(w)],[-np.diag(w),-G]])
    val,V=eig(A);sel=np.flatnonzero(val.imag>0)
    z=(1+val/(2*rate))/(1-val/(2*rate))
    residual=np.linalg.norm(A@V-V*val[None,:],axis=0)/np.maximum(np.linalg.norm(A@V,axis=0),1e-30)
    if max(residual)>1e-7 or max(abs(z))>1+1e-10:raise ValueError('unstable or invalid eigensolution')
    return val[sel],z[sel],U,V[:,sel],w,float(max(residual))

def participation(M,K,D,Q,regional,model,U,vec,w,pole,z,rate,local):
    n=len(w);q=U@(vec[:n]/w);v=U@vec[n:]
    E=.5*float(np.vdot(v,M@v).real+np.vdot(q,K@q).real)
    power=float(np.vdot(v,D@v).real)
    if E<=0 or power<0:raise ValueError('mode energy')
    a=model.a;b=a.n;parts=[]
    for j,wire in enumerate(a.wires):
        ids=slice(b+j*a.partials,b+(j+1)*a.partials)
        T=np.r_[a.A[j]@q[:b],wire.U[:,:a.partials]@q[ids]]
        S=np.r_[a.A[j]@v[:b],wire.U[:,:a.partials]@v[ids]]
        en=.5*float(np.vdot(S,wire.M@S).real+np.vdot(T,wire.K@T).real)
        loss=float(np.vdot(S,wire.D@S).real)
        parts.append(dict(wire=wire.id,energyFraction=en/E,intrinsicLossWPerJ=loss/E))
    board=.5*float(np.vdot(v[:b],v[:b]).real+np.vdot(q[:b],a.k*q[:b]).real)
    regions=[float(np.vdot(v[:b],g@v[:b]).real/E) for g in regional]
    damp=(model.d*abs(Q.T@v)**2/E).tolist()
    balance=abs(board/E+sum(x['energyFraction'] for x in parts)-1.)
    lossBalance=abs(sum(regions)+sum(damp)+sum(x['intrinsicLossWPerJ'] for x in parts)-power/E)
    identity=abs(power/E+2*pole.real)/max(power/E,abs(2*pole.real),1e-20)
    if balance>1e-7 or lossBalance>1e-7*max(power/E,1.) or identity>1e-5:raise ValueError('modal energy partition')
    f=abs(np.angle(z))*rate/(2*np.pi);decay=-rate*np.log(abs(z))
    pressureKernel=local[f'kernel_{rate}_3']
    # Evaluate FIR at the discrete eigenvalue, not a continuous frequency.
    H=np.einsum('t,mti->mi',z**(-np.arange(pressureKernel.shape[1])),pressureKernel)
    pr=H@((1-1/z)*rate*v[:b])/np.sqrt(E)
    return dict(digitalHz=float(f),continuousHz=float(pole.imag/(2*np.pi)),
        amplitudeDecayPerS=float(decay),t60S=float(np.log(1000)/decay) if decay>0 else None,
        boardEnergyFraction=board/E,wires=parts,regionalLossWPerJ=regions,damperLossWPerJ=damp,
        totalLossWPerJ=power/E,pressurePaPerSqrtJ=abs(pr).tolist(),
        energyPartitionRelative=balance,lossPartitionAbsolute=lossBalance,decayIdentity=identity)

def models(local,wires,rows,spread,factor,key,control,rate,n):
    ww,_=detune(wires,rows,spread);ww=copy.deepcopy(ww);groups=[w.port for w in ww]
    for j,w in enumerate(ww):w.port=j
    a=CoupledWire(local['stiffness'],local['damping']*factor,np.zeros((80,len(ww))),local['wirePorts'],ww,rate,n)
    B,I=damper_ports(a,rows);m=PointDense(a,B,I)
    groups=np.asarray(groups);d=2./np.bincount(groups)[groups]
    if control=='release_pedal':d[:]=0
    elif control=='held_no_pedal':d[groups==KEYS.index(key)]=0
    elif control!='release_no_pedal':raise ValueError('control')
    m.set_levels(d)
    return m

def inspect(local,wires,rows,cfg):
    key,control,spread,factor,rate,n=cfg
    m=models(local,wires,rows,spread,factor,key,control,rate,n);M,K,D=m.M,m.K,m.D
    vals,z,U,V,w,residual=pole_data(M,K,D,rate)
    freq=np.angle(z)*rate/(2*np.pi)
    targets=[('reported',f) for f in TARGETS]+[('fundamental',440*2**((key-69)/12))]
    results=[]
    for label,f in targets:
        # Keep three nearest, plus slowest within +/- 8 Hz if not already present.
        near=np.argsort(abs(freq-f))[:3];window=np.flatnonzero(abs(freq-f)<=8.)
        ids=list(near)
        if len(window):
            slow=window[np.argmax(abs(z[window]))]
            if slow not in ids:ids.append(slow)
        modes=[]
        for i in ids:
            data=participation(M,K,D,m.Q,local['regionalDamping']*factor,m,U,V[:,i],w,vals[i],z[i],rate,local)
            data['distanceHz']=float(abs(freq[i]-f));data['within8Hz']=bool(abs(freq[i]-f)<=8.)
            modes.append(data)
        results.append(dict(kind=label,targetHz=f,modes=modes))
    row=dict(key=key,control=control,spreadCents=spread,structureFactor=factor,rate=rate,partials=n,
        positiveFrequencyPoles=len(vals),maximumEigenResidual=residual,targets=results,
        maximumPoleMagnitude=float(max(abs(z))))
    print('G3_RESIDUAL_POLES_CASE '+json.dumps(row,allow_nan=False),flush=True)
    return row

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    local,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    configs=[(60,c,s,d,48000,32) for c in ('release_pedal','held_no_pedal','release_no_pedal') for s,d in ((0.,1.),(1.,.25))]
    configs += [(key,'release_pedal',0.,d,48000,32) for key in (45,48,64) for d in (1.,.25)]
    configs += [(60,c,0.,1.,rate,n) for c in ('release_pedal','release_no_pedal') for rate,n in ((96000,32),(48000,64))]
    cases=[inspect(local,wires,rows,cfg) for cfg in configs]
    summary=dict(gate=True,cases=len(cases),diagnosticOnly=True,calibratedParameters=False,modeExcitationProven=False,
        noAcousticFeedback=True,frequencyMatchNotCausation=True,above500HzDiagnosticOnly=True,
        maximumEigenResidual=max(v['maximumEigenResidual'] for v in cases),feedbackApproved=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'residual_poles.json').write_text(json.dumps(dict(summary=summary,cases=cases,sourceFrozenSha256=sha,
        pressureManifestSha256=ph,referenceManifestSha256=rh),indent=2,allow_nan=False))
    print('G3_RESIDUAL_POLES_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()

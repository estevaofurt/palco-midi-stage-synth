"""G3.13n: actual post-impact modal pressure attribution.
Reconstruct the existing dry WAV from the complete damped state, then
identify coherent contributions of reported frequency clusters.
No damping selection, no filtering or modification of output."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh,eig,solve
from scipy.io.wavfile import read
from wire_physical_midpoint import load,CoupledWire
from structural_passive_fit import read_reference
from dry_pressure_render import pressure_source,RATE,PARTIALS
from physical_pedal_repeat import PointSchur,PointDense,Repeating,damper_ports
from variable_damper import PedalControl
from felt_law import params
from distributed_felt import wire_loss
from residual_poles import participation
from split_radiation import relative

KEYS=(45,48,60,64)
TARGETS=(220.,327.,669.,783.,791.,1057.,1719.,1838.,1957.,2315.,2897.)
TIMES=(1.,5.,10.,15.)

def attack(local,wires,rows,groups,masses,felts,key,speed,scale):
    ww=wire_loss(wires,scale)
    for j,w in enumerate(ww):w.port=j
    a=CoupledWire(local['stiffness'],local['damping'],np.zeros((80,len(ww))),local['wirePorts'],ww,RATE,PARTIALS)
    B,I=damper_ports(a,rows);target=PointSchur(a,B,I);bank=Repeating(target,groups,masses,felts)
    ctrl=PedalControl(len(masses),RATE,transition_ms=5.);g=np.asarray(groups);strength=2./np.bincount(g)[g];j=KEYS.index(key)
    ctrl.sustain(1.);ctrl.note(j,True);bank.launch(j,speed)
    for t in range(round(.030*RATE)):
        if t==round(.020*RATE):ctrl.note(j,False)
        bank.damp(strength*ctrl.advance()[g]);bank.step()
    if bank.captures!=1 or np.any(bank.active) or np.any(target.d):raise ValueError('attack not settled')
    error=abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss-bank.injected)/bank.injected
    if error>1e-8:raise ValueError('attack energy')
    m=PointDense(a,B,I);q,v=target.state()
    return m,q,v,error

def basis(M,K,D,rate):
    lam,U=eigh(K,M)
    if min(lam)<=0:raise ValueError('nonpositive stiffness')
    w=np.sqrt(lam);n=len(w);G=U.T@D@U
    A=np.block([[np.zeros((n,n)),np.diag(w)],[-np.diag(w),-G]])
    pole,V=eig(A);z=(1+pole/(2*rate))/(1-pole/(2*rate))
    residual=np.linalg.norm(A@V-V*pole[None,:],axis=0)/np.maximum(np.linalg.norm(A@V,axis=0),1e-30)
    if max(residual)>1e-7 or max(abs(z))>1+1e-10:raise ValueError('pole accuracy/stability')
    return U,w,pole,z,V,float(max(residual))

def coefficients(M,U,w,V,q,v):
    x=np.r_[w*(U.T@M@q),U.T@M@v];c=solve(V,x)
    error=relative(V@c,x)
    if error>1e-8:raise ValueError('state reconstruction')
    return c,error

def pressure_coefficients(U,V,z,c,kernel,rate):
    n=len(U);board=U[:kernel.shape[2],:]@V[n:,:]
    H=np.einsum('ti,mta->mai',z[None,:]**(-np.arange(kernel.shape[1])[:,None]),kernel,optimize=True)
    # First tail output corresponds to (v_1-v_0)/h. For indices
    # beyond the FIR history this is exact for the free midpoint.
    return np.einsum('mai,ai->mi',H,board)*((z-1)*rate*c)[None,:]

def pressure_window(z,p,start,count,rate):
    # Use complete complex spectrum; conjugate modes are retained.
    if not len(z):return np.zeros((count,p.shape[0])),0.
    y=np.exp(np.arange(start,start+count,dtype=float)[:,None]*np.log(z)[None,:])@p.T
    error=float(np.linalg.norm(y.imag)/max(np.linalg.norm(y.real),1e-30))
    return y.real,error

def rms(y):return np.sqrt(np.mean(y*y,axis=0))
def candidate_rows(m,local,U,w,pole,z,V,ids):
    rows=[]
    for i in ids:
        # Positive branch only. Keep the actual radiation and physical
        # energy partition, not merely the closest frequency.
        if pole[i].imag<=0:continue
        v=participation(m.M,m.K,m.D,m.Q,local['regionalDamping'],m,U,V[:,i],w,pole[i],z[i],RATE,local)
        rows.append(dict(index=int(i),frequencyHz=v['digitalHz'],t60S=v['t60S'],
            boardEnergyFraction=v['boardEnergyFraction'],wires=[x for x in v['wires'] if x['energyFraction']>.01],
            pressurePaPerSqrtJ=v['pressurePaPerSqrtJ']))
    return rows

def analyze(m,local,q,v,wav,key,prepared):
    U,w,pole,z,V,eigen=prepared;c,state=coefficients(m.M,U,w,V,q,v)
    p=pressure_coefficients(U,V,z,c,local['kernel_48000_3'],RATE)
    f=np.abs(np.angle(z))*RATE/(2*np.pi)
    targets=[('fundamental',440*2**((key-69)/12))]+[('reported',x) for x in TARGETS]
    clusters=[]
    for label,hz in targets:
        ids=np.flatnonzero(abs(f-hz)<=4.)
        modes=candidate_rows(m,local,U,w,pole,z,V,ids)
        clusters.append((label,hz,ids,modes))
    replay=[];records=[];offset=round(.030*RATE);count=4096
    for t in TIMES:
        start=round(t*RATE)-offset
        actual=wav[start+offset:start+offset+count].astype(float)
        full,imag=pressure_window(z,p,start,count,RATE)
        absolute=float(np.linalg.norm(full-actual)/np.sqrt(actual.size))
        err=relative(full,actual);scale=max(float(np.max(abs(wav[:RATE]))),1e-30)
        # Absolute fallback only below -120 dB RMS relative to initial
        # peak, where the near-zero reference makes relative error unhelpful.
        accepted=err<=1e-4 or absolute<=scale*1e-6
        replay.append(dict(timeS=t,relative=err,absoluteRmsPa=absolute,imaginaryRelative=imag,gate=bool(accepted and imag<=1e-5)))
        row=[]
        for label,hz,ids,modes in clusters:
            y,im=pressure_window(z[ids],p[:,ids],start,count,RATE)
            amp=rms(y);fullr=rms(full)
            # Ratios are coherent cluster RMS, not additive modal energies;
            # overlapping clusters and interference may yield ratios >1.
            row.append(dict(kind=label,targetHz=hz,modeCount=len(ids),rmsPa=amp.tolist(),
                relativeToFullRms=(amp/np.maximum(fullr,1e-30)).tolist(),imaginaryRelative=im))
        records.append(dict(timeS=t,fullRmsPa=rms(full).tolist(),clusters=row))
    if not all(v['gate'] for v in replay):raise ValueError('WAV modal replay: '+str(replay))
    return dict(eigenResidual=eigen,stateReplay=state,pressureReplay=replay,
        clusters=[dict(kind=l,targetHz=f,modes=modes) for l,f,ids,modes in clusters],windows=records)

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','nominal','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--key',type=int,choices=KEYS,required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    local,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    raw=(a.nominal/'distributed_felt_loss.json').read_bytes();d=json.loads(raw);s=d['summary']
    if any(s.get(k)!=v for k,v in dict(gate=True,cases=6,group=f'{a.key}-release_pedal',sourceFrozenSha256=sha,
        pressureManifestSha256=ph,referenceManifestSha256=rh,noOutputEQ=True,acousticFeedbackIncluded=False).items()):raise ValueError('nominal source')
    results=[];cache={}
    for row in d['results']:
        speed=row['hammerSpeedMps'];scale=row['wireStiffnessLossScale']
        item=row['pressure'];path=a.nominal/item['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('WAV hash')
        rate,wav=read(path)
        if rate!=RATE or wav.dtype!=np.float32 or wav.shape!=(1921440,2):raise ValueError('WAV format')
        m,q,v,bal=attack(local,wires,rows,groups,masses,felts,a.key,speed,scale)
        if scale not in cache:cache[scale]=basis(m.M,m.K,m.D,RATE)
        value=analyze(m,local,q,v,wav,a.key,cache[scale])
        result=dict(key=a.key,speed=speed,lossScale=scale,attackBalance=bal,**value);results.append(result)
        print('G3_EXCITED_RESIDUAL_CASE '+json.dumps(result,allow_nan=False),flush=True)
    summary=dict(gate=True,cases=len(results),key=a.key,diagnosticOnly=True,calibratedParameters=False,
        actualAttackState=True,coherentPressureClusters=True,frequencyMatchOnly=False,
        acousticFeedbackIncluded=False,above500HzDiagnosticOnly=True,
        maximumPressureReplayRelative=max(x['relative'] for v in results for x in v['pressureReplay']),
        maximumStateReplay=max(v['stateReplay'] for v in results),
        sourceFrozenSha256=sha,pressureManifestSha256=ph,nominalManifestSha256=hashlib.sha256(raw).hexdigest())
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'excited_residuals.json').write_text(json.dumps(dict(summary=summary,results=results),indent=2,allow_nan=False))
    print('G3_EXCITED_RESIDUAL_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()

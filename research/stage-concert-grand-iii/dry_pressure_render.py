"""G3.13e: experimental dry physical C4 -> retarded pressure WAV.
No feedback, no cabinet, no fitted envelope or calibrated audibility.
Common gain for all audition files; preserve raw pressure separately."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.io.wavfile import write,read as read_wav
from scipy.signal import butter,sosfilt
from wire_physical_midpoint import load,CoupledWire
from compiled_wire_midpoint import Compiled
from physical_pedal_repeat import PointSchur,Repeating,damper_ports
from variable_damper import PedalControl
from physical_unison_decay import detune
from physical_loss_sensitivity import crossings
from felt_law import params
from causal_pressure_observer import Observer,TRAIN,HIGH,transfer
from physical_long_decay import startup
from wire_port_enrichment import development_grids,comparison
from modal_string_radiation import response
from structural_passive_fit import read_reference
from wire_baffle_reference import FREQ
from acoustic_matrix_archive import read_npz
from split_radiation import relative

RATE=48000
PARTIALS=32
CASES=[(0.,1.,.3),(0.,1.,3.),(1.,.25,.3),(1.,.25,3.)]

def align_coordinates(local,reference):
    # q_reference = T @ q_local. Derive T from the *physical* lift,
    # not from modal index or individual eigenvector sign assumptions.
    L=reference['physicalLift'];R=local['physicalLift']
    if L.shape!=R.shape or L.ndim!=2 or not np.isfinite(L).all() or not np.isfinite(R).all():
        raise ValueError('physical lift dimensions')
    scale=np.maximum(np.maximum(np.linalg.norm(L,axis=1),np.linalg.norm(R,axis=1)),1e-12*np.max(abs(L)))
    T,_,rank,sv=np.linalg.lstsq(L/scale[:,None],R/scale[:,None],rcond=1e-12)
    n=L.shape[1]
    if rank!=n:raise ValueError('physical lift rank')
    U,_,V=np.linalg.svd(T,full_matrices=False);Q=U@V
    e=dict(rawOrthogonality=relative(T.T@T,np.eye(n)),orthogonalCorrection=relative(T,Q),
        physicalLift=relative(L@Q,R),stiffness=relative(Q.T@np.diag(reference['stiffness'])@Q,np.diag(local['stiffness'])),
        damping=relative(Q.T@reference['damping']@Q,local['damping']),
        ports=relative(Q.T@reference['ports'],local['ports']),
        wirePorts=relative(reference['wirePorts']@Q,local['wirePorts']),
        regionalDamping=relative(np.stack([Q.T@g@Q for g in reference['regionalDamping']]),local['regionalDamping']))
    # Compare the complex pressure maps at every common archived frequency.
    common=sorted(set(FREQ)&set(TRAIN+HIGH))
    if not common:raise ValueError('no common pressure reference')
    e['pressure']=max(relative(reference['pressure'][FREQ.index(f)]@reference['fieldMap']@Q,
        local['pressureReference'][(TRAIN+HIGH).index(f)]) for f in common)
    print('G3_DRY_PRESSURE_COORDINATE_AUDIT '+json.dumps(dict(errors=e,rank=int(rank),
        condition=float(sv[0]/sv[-1]),commonFrequenciesHz=common),allow_nan=False),flush=True)
    if max(e.values())>1e-7:raise ValueError('physical coordinate congruence failed: '+str(e))
    # The renderer uses ONLY local mechanics and local pressure kernels.
    # Q is an audit, not a modification of either archive.
    return dict(errors=e,commonFrequenciesHz=common,rank=int(rank),
        condition=float(sv[0]/sv[-1]),usesLocalMechanicsAndPressure=True)

def observable_audit(local,reference,archive,wires):
    # Independent reductions can span different physical subspaces. Do
    # not identify their columns. Compare external transfer functions
    # in the same force-port coordinates, never mix their matrices.
    freq=np.sort(np.r_[tuple(development_grids())[0],tuple(development_grids())[1],tuple(development_grids())[2]])
    reports=[]
    for n in (16,32,128):
        models=[CoupledWire(z['stiffness'],z['damping'],z['ports'],z['wirePorts'],wires,RATE,n) for z in (local,archive,reference)]
        y=models[0].transfer(freq)
        reports.append(dict(partials=n,frozen= comparison(y,models[1].transfer(freq)),baffle=comparison(y,models[2].transfer(freq))))
    mobility=max(max(v['frozen']['maximum'],v['baffle']['maximum']) for v in reports)
    # Check the pressure kernel against the independent harmonic
    # pressure archive belonging to THIS local mechanical model.
    H=transfer(local['kernel_48000_3'],TRAIN,RATE)* (2j*np.pi*np.asarray(TRAIN))[:,None,None]
    pressure=max(relative(h,local['pressureReference'][i]) for i,h in enumerate(H))
    G=local['regionalDamping'];d=local['damping']
    damping=relative(G.sum(axis=0),d)
    minimum=min(float(np.linalg.eigvalsh(g).min()/max(np.linalg.norm(g),1e-30)) for g in G)
    if min(local['stiffness'])<=0:raise ValueError('nonpositive local stiffness')
    # Compare physical pressure outputs at shared frequencies for
    # information, not a license to substitute the other basis.
    common=sorted(set(FREQ)&set(TRAIN));external=[]
    for f in common:
        i=FREQ.index(f);j=TRAIN.index(f);outputs=[]
        for z,observer in ((local,local['pressureReference'][j]),(reference,reference['pressure'][i]@reference['fieldMap'])):
            md=dict(M=np.eye(80),K=np.diag(z['stiffness']),D=z['damping'],P=z['ports'])
            Y,O,a=response(md,z['wirePorts'],wires,np.zeros((80,80),complex),observer,f)
            if not a['gate']:raise ValueError('dry harmonic algebra')
            outputs.append((Y,O))
        external.append(dict(frequencyHz=f,mobility=relative(outputs[0][0],outputs[1][0]),pressure=relative(outputs[0][1],outputs[1][1])))
    report=dict(dryTransfer=reports,maximumDryTransfer=mobility,localPressureKernel=pressure,
        dampingPartition=damping,minimumRegionalDamping=minimum,independentPressureComparison=external,
        independentPressureAgreementGate=all(x['pressure']<=.05 for x in external),
        usesLocalMechanicsAndPressure=True,crossBasisMatricesMixed=False)
    print('G3_DRY_PRESSURE_OBSERVABLE_AUDIT '+json.dumps(report,allow_nan=False),flush=True)
    if mobility>1e-5 or pressure>.005 or damping>1e-10 or minimum<-1e-10:
        raise ValueError('local model observable replay failed')
    return report

def pressure_source(root,sha,reference,archive,wires):
    raw=(root/'causal_pressure_observer.json').read_bytes();d=json.loads(raw);s=d['summary']
    expected=dict(gate=True,structureRank=80,cases=4,causalDelayObserver=True,sameCoordinateSurface=True,
        acousticFeedbackIncluded=False,validatedBandHz=[30,500],calibratedParameters=False)
    if d['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in expected.items()):raise ValueError('pressure source')
    shapes=dict(stiffness=(80,),damping=(80,80),ports=(80,7),wirePorts=(10,80),
        physicalLift=(1386,80),regionalDamping=(3,80,80),microphoneXYZ=(2,3),pressureReference=(len(TRAIN+HIGH),2,80))
    for row in d['cases']:shapes[f"kernel_{row['rate']}_{row['degree']}"]=(2,row['taps'],80)
    z=read_npz(root,d['archive'],shapes,TRAIN+HIGH)
    # The earlier strict congruence test remains available for archives
    # intended to share a coordinate system. This render requires no such
    # congruence: all its dynamics and pressure maps come from one archive.
    audit=observable_audit(z,reference,archive,wires)
    return z,audit,hashlib.sha256(raw).hexdigest()

def render(z,wires,rows,groups,masses,felts,spread,factor,speed,seconds=40.):
    ww,_=detune(wires,rows,spread);ww=copy.deepcopy(ww)
    for j,w in enumerate(ww):w.port=j
    rate=RATE;n=PARTIALS
    a=Compiled(z['stiffness'],z['damping']*factor,np.zeros((80,len(ww))),z['wirePorts'],ww,rate,n)
    B,I=damper_ports(a,rows);target=PointSchur(a,B,I)
    bank=Repeating(target,groups,masses,felts);ctrl=PedalControl(len(masses),rate,transition_ms=5.)
    groups=np.asarray(groups);strength=2./np.bincount(groups)[groups]
    ctrl.sustain(1.);ctrl.note(2,True);bank.launch(2,speed)
    count=round(.030*rate);acc=np.empty((count,80))
    for t in range(count):
        if t==round(.020*rate):ctrl.note(2,False)
        bank.damp(strength*ctrl.advance()[groups]);old=a.v.copy();bank.step()
        acc[t]=(a.v-old)*rate
    if bank.captures!=1 or np.any(bank.active) or np.any(target.d):raise ValueError('unsettled startup')
    E0=a.energy();init=abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss-bank.injected)/bank.injected
    if init>1e-8:raise ValueError('attack energy')
    observer=Observer(z['kernel_48000_3'],rate)
    pieces=[observer.process(acc)];tail=round(seconds*rate);loss=error=0.
    for start in range(0,tail,4096):
        m=min(4096,tail-start);F=np.zeros((m,len(ww)));O=F.copy();L=np.zeros((m,2));acc=np.zeros((m,80))
        a.process(F,O,L,acc)
        if np.any(L[:,0]) or L[:,1].min()<-E0*1e-12:raise ValueError('tail work/loss')
        loss+=float(L[:,1].sum());error=max(error,abs(a.energy()+loss-E0)/E0)
        pieces.append(observer.process(acc))
    y=np.concatenate(pieces)
    if not np.isfinite(y).all() or np.max(abs(y))<=0 or error>1e-8:raise ValueError('render energy/signal')
    rms=np.sqrt(np.mean(y[count:].reshape(-1,2400,2)**2,axis=1))
    # Separate causal lowpass for in-band diagnostic, no normalization of individual notes.
    filtered=sosfilt(butter(4,500,fs=rate,output='sos'),y,axis=0)
    band=np.sqrt(np.mean(filtered[count:].reshape(-1,2400,2)**2,axis=1))
    return y,filtered,rms,band,dict(spreadCents=spread,structureFactor=factor,hammerSpeedMps=speed,
        injectedJ=bank.injected,mechanicalEnergyJ=E0,startupBalance=init,tailBalance=error,peakPressurePa=np.max(abs(y),axis=0).tolist(),
        fullPedal=True,startupSamples=count,samples=len(y),tailSeconds=seconds)

def common_gain(ys):
    peak=max(float(np.max(abs(y))) for y in ys)
    if peak<=0 or not np.isfinite(peak):raise ValueError('peak')
    return .8/peak

def pcm(y,gain):
    x=y*gain
    if not np.isfinite(x).all() or np.max(abs(x))>1.:raise ValueError('clipping')
    return np.rint(x*32767).astype(np.int16)

def export_wav(path,signal,gain,physical_units=False):
    payload=signal.astype(np.float32) if physical_units else pcm(signal,gain)
    write(path,RATE,payload)
    rate,check=read_wav(path)
    if rate!=RATE or check.shape!=payload.shape or check.dtype!=payload.dtype or not np.array_equal(check,payload):
        raise ValueError('WAV round-trip mismatch: '+path.name)
    if not np.isfinite(check).all() or not np.any(check):raise ValueError('empty WAV: '+path.name)
    if not physical_units and np.max(abs(check.astype(np.int32)))>=32767:raise ValueError('clipped PCM')
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        sampleRate=rate,samples=len(check),channels=check.shape[1],dtype=str(check.dtype),
        peak=float(np.max(abs(check.astype(np.float64)))),roundTripExact=True)

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','joint','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    joint_raw=(a.joint/'physical_joint_decay.json').read_bytes();d=json.loads(joint_raw)
    if d['sourceFrozenSha256']!=sha or any(d['summary'].get(k)!=v for k,v in dict(gate=True,cases=42,fullAttackRecomputed=True,acousticLoadIncluded=False).items()):
        raise ValueError('joint source')
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']};keys=[45,48,60,64]
    pars=[params(k,rows[k]['count'],spec,felt) for k in keys];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    rows['_platePort']=z['ports'][:,6]
    a.out.mkdir(parents=True,exist_ok=True);renders=[]
    for spread,factor,speed in CASES:
        y,b,rms,band,row=render(z,wires,rows,groups,masses,felts,spread,factor,speed)
        prior=next(x for x in d['cases'] if x['rate']==RATE and x['spreadCents']==spread and x['structureFactor']==factor and x['hammerSpeedMps']==speed)
        # Independent replay of startup using the uncompiled midpoint path
        # in the same local basis. Cross-basis prior remains diagnostic.
        ww,_=detune(wires,rows,spread)
        m,q,v,O,initial=startup(z['stiffness'],z['damping']*factor,z['wirePorts'],ww,rows,groups,masses,felts,RATE,PARTIALS,1.,speed)
        e=abs(row['mechanicalEnergyJ']/initial['mechanicalEnergyJ']-1.)
        if e>1e-7:raise ValueError('local attack replay')
        row['attackReplayRelative']=e
        row['priorIndependentAttackEnergyRelative']=abs(row['mechanicalEnergyJ']/prior['mechanicalEnergyJ']-1.)
        renders.append((y,b,rms,band,row))
        print('G3_DRY_PRESSURE_RENDER_CASE '+json.dumps(row,allow_nan=False),flush=True)
    gain=common_gain([v for y,b,*_ in renders for v in (y,b)])
    ref=renders[1][2].max(axis=0);bref=renders[1][3].max(axis=0);cases=[]
    for y,b,rms,band,row in renders:
        name=('nominal' if row['spreadCents']==0. else 'unison1_damping25')+('_weak' if row['hammerSpeedMps']==.3 else '_strong')
        files={}
        for suffix,signal,physical_units in [('pressure_pa',y,True),('audition_40s',y,False),('audition_5s',y[:5*RATE],False),('lowpass500_5s',b[:5*RATE],False)]:
            path=a.out/(name+'_'+suffix+'.wav')
            files[suffix]=export_wav(path,signal,gain,physical_units)
        row.update(files=files,commonPressureThresholds=[crossings(rms[:,i],ref[i]) for i in range(2)],
            commonLowpassThresholds=[crossings(band[:,i],bref[i]) for i in range(2)])
        cases.append(row)
        print('G3_DRY_PRESSURE_RENDER_RESULT '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=True,wavFiles=sum(len(v['files']) for v in cases),wavRoundTripExact=True,cases=len(cases),diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,
        sampleRate=RATE,partials=PARTIALS,structureRank=80,wires=10,key=60,commonAuditionGain=gain,
        noEnvelope=True,acousticFeedbackIncluded=False,oneSidedIdealBaffle=True,validatedObserverBandHz=[30,500],
        fullBandDiagnosticOnly=True,lowpass500IsNotBrickwall=True,audibleSustainMeasured=False,
        crossBasisMatricesMixed=False,independentPressureAgreementGate=coord['independentPressureAgreementGate'],
        maximumPriorIndependentAttackEnergyRelative=max(v['priorIndependentAttackEnergyRelative'] for v in cases),
        maximumEnergyError=max(max(v['startupBalance'],v['tailBalance']) for v in cases),
        maximumAttackReplay=max(v['attackReplayRelative'] for v in cases),timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'dry_pressure_render.json').write_text(json.dumps(dict(summary=summary,cases=cases,coordinateReplay=coord,
        sourceFrozenSha256=sha,referenceManifestSha256=rh,pressureManifestSha256=ph,jointManifestSha256=hashlib.sha256(joint_raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_DRY_PRESSURE_RENDER_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()

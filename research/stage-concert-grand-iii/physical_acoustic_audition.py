"""G3.14d.15: gated 5-second offline C4 pressure audition.
Same local structural basis for mechanics, CQ and causal pressure.
No output EQ, normalization per note/variant, or sustain claim."""
import copy,json,time
from pathlib import Path
import numpy as np
from acoustic_contact import AcousticSchur
from wire_acoustic_port import WireAcoustic
from partitioned_acoustic_memory import PartitionedMemory
from physical_pedal_repeat import Repeating,damper_ports
from variable_damper import PedalControl
from felt_law import params
from causal_pressure_observer import Observer,build_kernel,stream_proof,harmonic_proof
from unison_profiles import KEYS,profiles_for_key,detune_profile
from mode_selective_loss import mode_loss
from attack_flutter import envelope_metrics,episodes,write_checked
from sustain_brightness import attack_bands,attack_compare
from dry_pressure_render import common_gain
from split_radiation import relative

class PartitionedContact(AcousticSchur):
    def init_memory(self,U,W):
        self.projection=U;self.weights=W
        self.engine=PartitionedMemory(W,64) if len(W)>1 else None
        self.empty=np.zeros(U.shape[1]);self.air=0.;self.minimumAir=0.
    def memory(self):
        # Contact prediction can read history repeatedly without advancing it.
        return self.engine.past() if self.engine is not None else self.empty.copy()
    def advance(self,v,mem):
        y=self.projection.T@v;f=self.weights[0]@y+mem
        self.air+=self.h*float(y@f);self.minimumAir=min(self.minimumAir,self.air)
        if self.engine is not None:self.engine.push(y)

def render(k,D,A,wires,rows,U,W,K,rate,speed,wet,seconds=5.):
    key=60;j=KEYS.index(key);n=32
    groups=[w.port for w in wires]
    root=Path(__file__).parent
    spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    pars=[params(key0,rows[key0]['count'],spec,felt) for key0 in KEYS]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    ww,_=detune_profile(copy.deepcopy(wires),rows,profiles_for_key(key)[0][1]);ww=mode_loss(ww,4.,4.)
    for i,w in enumerate(ww):w.port=i
    if not wet:W=np.zeros((1,U.shape[1],U.shape[1]))
    a=WireAcoustic(k,D,np.zeros((len(k),len(ww))),A,ww,rate,n,U,W)
    B,I=damper_ports(a,rows);target=PartitionedContact(a,B,I)
    bank=Repeating(target,groups,masses,felts);ctrl=PedalControl(len(masses),rate,transition_ms=5.)
    g=np.asarray(groups);strength=2./np.bincount(g)[g]
    # Match the nominal attack control, including opening transition.
    ctrl.sustain(1.);ctrl.note(j,True);bank.launch(j,speed)
    count=round(.030*rate);total=round(seconds*rate);force=np.empty((count,len(ww)))
    pressure=Observer(K,rate);pieces=[];acc=np.empty((min(4096,total),len(k)));pos=0
    injected=bank.injected;attackBalance=tailBalance=loss=0.;E0=air0=None
    start=time.perf_counter()
    F=np.zeros(len(ww))
    for t in range(total):
        old=a.v.copy()
        if t<count:
            if t==round(.020*rate):ctrl.note(j,False)
            bank.damp(strength*ctrl.advance()[g]);force[t]=bank.step()[0]
            attackBalance=max(attackBalance,abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss+target.air-injected)/injected)
            if t==count-1:
                if bank.captures!=1 or np.any(bank.active) or np.any(target.d):raise ValueError('unsettled attack')
                E0=a.energy();air0=target.air
        else:
            _,_,l=target.step(F);loss+=l
            if t%256==0 or t==total-1:
                tailBalance=max(tailBalance,abs(a.energy()+loss+target.air-air0-E0)/max(E0,1e-30))
        acc[pos]=(a.v-old)*rate;pos+=1
        if pos==len(acc) or t==total-1:pieces.append(pressure.process(acc[:pos]));pos=0
    y=np.concatenate(pieces)
    minAir=target.minimumAir/injected
    if max(attackBalance,tailBalance)>1e-8 or minAir<-1e-8 or not np.isfinite(y).all() or not np.any(y):raise ValueError('physical audition energy gate')
    return y,dict(key=key,speed=speed,wet=wet,seconds=seconds,attackBalance=attackBalance,tailBalance=tailBalance,
        minimumAcousticWorkRelative=minAir,acousticWorkJ=target.air,injectedJ=injected,finalMechanicalEnergyJ=a.energy(),
        captures=bank.captures,hammerContacts=episodes(force,rate),pressureEnvelope=envelope_metrics(y[:2*rate],rate,key),
        attackBands=attack_bands(y,rate),renderSeconds=time.perf_counter()-start)

def audition(out,k,D,A,wires,rows,U,W,geom,rate,refs,sourceHash,projectionHash):
    B,_,quad,_,mic,_=geom;xy,w,S=quad[3:];S=S@B
    K,support,_=build_kernel(xy,w,S,mic,rate,3)
    proof=stream_proof(K,rate,support)
    freqs=sorted(refs);harm=harmonic_proof(K,rate,xy,w,S,mic,freqs)
    band=max(max(v['accelerationRelative'],v['velocityRelative']) for v in harm)
    if not proof['gate'] or band>.005:raise ValueError('local pressure observer gate')
    out.mkdir(parents=True,exist_ok=True);renders=[]
    for speed in (.3,3.):
        baseline=None
        for wet in (False,True):
            y,row=render(k,D,A,wires,rows,U,W,K,rate,speed,wet)
            if not wet:baseline=row
            row['attackComparison']=attack_compare(row['attackBands'],baseline['attackBands'])
            renders.append((y,row))
            print('G3_PHYSICAL_AUDITION_CASE '+json.dumps(row,allow_nan=False),flush=True)
    gain=common_gain([v[0] for v in renders]);results=[]
    for y,row in renders:
        label='C4_'+('weak' if row['speed']==.3 else 'strong')+'_'+('wet' if row['wet'] else 'dry')
        row['listen']=write_checked(out/(label+'_5s.wav'),y,rate,False,gain)
        row['native']=write_checked(out/(label+'_pressure_5s.wav'),y,rate,True,gain)
        results.append(row)
    summary=dict(gate=True,diagnosticOnly=True,cases=len(results),seconds=5,rate=rate,rank=U.shape[1],
        commonGain=gain,noOutputEQ=True,localBasis=True,physicalAcousticHypothesis=True,
        pressureBandMaximum=band,pressureStream=proof,sourceFrozenSha256=sourceHash,projectionFrozenSha256=projectionHash,
        approvedAttackReplayed=False,listenerApproved=False,above500HzDiagnosticOnly=True,
        audibleSustainMeasured=False,wholeEngineRealtimeValidated=False,physicalFeedbackAccepted=False)
    (out/'physical_audition.json').write_text(json.dumps(dict(summary=summary,cases=results),indent=2,allow_nan=False))
    print('G3_PHYSICAL_AUDITION_GATE '+json.dumps(summary,allow_nan=False),flush=True)

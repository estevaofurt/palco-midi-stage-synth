"""G3.13v: exact discrete energy ledger for each wire and the board.
Independent diagnostic: no changes to compiled dynamics or output EQ.
Net bridge work per block is not instantaneous gross transfer."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from numba import njit
from compiled_wire_midpoint import Compiled,kernel
from physical_pedal_repeat import PointSchur,Repeating,damper_ports
from variable_damper import PedalControl
from wire_physical_midpoint import load
from structural_passive_fit import read_reference
from dry_pressure_render import pressure_source
from causal_pressure_observer import Observer
from felt_law import params
from mode_selective_loss import mode_loss
from nominal_unison import approved_source
from unison_profiles import KEYS,profiles_for_key,detune_profile
from split_radiation import relative

def energies(a):
    rq=a.A@a.q;rv=a.A@a.v
    board=.5*(a.v@a.v+np.sum(a.k*a.q*a.q))
    wire=.5*(a.m0*rv**2+2*rv*np.sum(a.mi*a.u,axis=1)+np.sum(a.u*a.u,axis=1)
        +a.k0*rq**2+2*rq*np.sum(a.ki*a.x,axis=1)+np.sum(a.ks*a.x*a.x,axis=1))
    return np.r_[board,wire]

@njit(cache=True)
def audited_kernel(h,k,D,A,P,ports,hammer,m0,k0,d0,mi,ki,di,ks,ds,C,invHi,J,
                   q,v,x,u,rv,rq,rm,ri,rb,vm,um,F,O,L,acc,loss):
    # Original numerical step is called unchanged, then its midpoint
    # velocities are used to independently attribute the physical dissipation.
    for t in range(len(F)):
        kernel(h,k,D,A,P,ports,hammer,m0,k0,d0,mi,ki,di,ks,ds,C,invHi,J,
               q,v,x,u,rv,rq,rm,ri,rb,vm,um,F[t:t+1],O[t:t+1],L[t:t+1],acc[t:t+1])
        for j in range(len(vm)):
            for i in range(len(vm)):
                loss[0]+=h*vm[j]*D[j,i]*vm[i]
        for w in range(len(x)):
            b=0.
            for j in range(len(vm)):b+=A[w,j]*vm[j]
            s=d0[w]*b*b
            for i in range(x.shape[1]):
                s+=ds[w,i]*um[w,i]**2+2*di[w,i]*b*um[w,i]
            loss[w+1]+=h*s

def step_block(a,count):
    F=np.zeros((count,a.P.shape[1]));O=F.copy();L=np.zeros((count,2))
    acc=np.empty((count,a.n));loss=np.zeros(a.nw+1)
    audited_kernel(a.h,a.k,a.D,a.A,a.P,a.ports,a.hammer,a.m0,a.k0,a.d0,a.mi,a.ki,a.di,a.ks,a.ds,a.C,a.invHi,a.J,
                   a.q,a.v,a.x,a.u,a.rv,a.rq,a.rm,a.ri,a.rb,a.vm,a.um,F,O,L,acc,loss)
    return acc,loss,float(L[:,1].sum())

def balance_step(before,after,loss,original_loss,initial):
    if not all(np.isfinite(x).all() for x in (before,after,loss)) or initial<=0:raise ValueError('nonfinite ledger')
    if min(after)<-initial*1e-10 or min(loss)<-initial*1e-10:raise ValueError('negative component')
    net=after-before+loss
    error=max(abs(net.sum()),abs(loss.sum()-original_loss))/initial
    if error>1e-8:raise ValueError('partition balance '+str(error))
    return net,error

def start(z,wires,rows,groups,masses,felts,key,speed):
    rate=48000;ww=mode_loss(wires,4.,2. if key==64 else 4.)
    for j,w in enumerate(ww):w.port=j
    a=Compiled(z['stiffness'],z['damping'],np.zeros((80,len(ww))),z['wirePorts'],ww,rate,32)
    B,I=damper_ports(a,rows);target=PointSchur(a,B,I)
    bank=Repeating(target,groups,masses,felts);ctrl=PedalControl(len(masses),rate,transition_ms=5.)
    g=np.asarray(groups);strength=2./np.bincount(g)[g];j=KEYS.index(key)
    ctrl.sustain(1.);ctrl.note(j,True);bank.launch(j,speed)
    acc=np.empty((1440,80))
    for t in range(len(acc)):
        if t==960:ctrl.note(j,False)
        bank.damp(strength*ctrl.advance()[g]);old=a.v.copy()
        bank.step();acc[t]=(a.v-old)*rate
    if bank.captures!=1 or np.any(bank.active) or np.any(target.d):raise ValueError('unsettled attack')
    e=abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss-bank.injected)/bank.injected
    if e>1e-8:raise ValueError('attack balance')
    obs=Observer(z['kernel_48000_3'],rate)
    return a,obs,obs.process(acc),e

def run_case(z,wires,rows,groups,masses,felts,key,speed,approved,baseline):
    a,obs,attack,attack_error=start(z,wires,rows,groups,masses,felts,key,speed)
    initial=energies(a);E0=a.energy()
    if E0<=0 or abs(initial.sum()-E0)/E0>1e-10:raise ValueError('initial partition')
    prev=initial;losses=np.zeros_like(initial);net=np.zeros_like(initial)
    incoming=net.copy();outgoing=net.copy();error=0.;replay=[attack];snapshots=[]
    # 50ms windows from hammer capture, split at the exact 2s attack boundary.
    pos=1440;end=1920000
    while pos<end:
        count=min(2400,end-pos)
        if pos<96000:count=min(count,96000-pos)
        acc,loss,original=step_block(a,count);pos+=count
        after=energies(a);work,err=balance_step(prev,after,loss,original,E0)
        losses+=loss;net+=work;incoming+=np.maximum(work,0.);outgoing+=np.maximum(-work,0.)
        error=max(error,err,abs(after.sum()-a.energy())/E0,abs(after.sum()+losses.sum()-E0)/E0)
        if error>1e-8:raise ValueError('cumulative balance')
        if pos<=96000:replay.append(obs.process(acc))
        if pos==96000 or pos==end or pos//48000!=(pos-count)//48000:
            snapshots.append(dict(timeS=pos/48000,energyFraction=(after/E0).tolist(),
                lossFraction=(losses/E0).tolist(),netBridgeWorkFraction=(net/E0).tolist(),
                positiveWindowNetFraction=(incoming/E0).tolist(),negativeWindowNetFraction=(outgoing/E0).tolist()))
        prev=after
    y=np.concatenate(replay);err=relative(y,approved.astype(float))
    if baseline and err>1e-6:raise ValueError('approved attack replay '+str(err))
    return dict(speed=speed,initialEnergyJ=E0,initialEnergyFraction=(initial/E0).tolist(),
        approvedAttackRelative=err,attackBalance=attack_error,maximumPartitionError=error,
        components=['board']+[w.id for w in a.wires],snapshots=snapshots)

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','reference','pressure','approved','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--key',type=int,choices=(48,60),required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,_,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    cases=[]
    for name,profile in profiles_for_key(a.key):
        if name not in ('approved','other_half','central_two'):continue
        ww,records=detune_profile(wires,rows,profile)
        for speed in (.3,3.):
            approved,ah=approved_source(a.approved,a.key,sha,ph,rh,speed)
            row=run_case(z,ww,rows,groups,masses,felts,a.key,speed,approved,name=='approved')
            row.update(variant=name,profile=list(profile),tuning=records,approvedManifestSha256=ah)
            cases.append(row)
            print('G3_BRIDGE_ENERGY_CASE '+json.dumps({k:v for k,v in row.items() if k!='snapshots'},allow_nan=False),flush=True)
    summary=dict(gate=True,key=a.key,cases=len(cases),diagnosticOnly=True,selectedParameters=None,
        nominalStructure=True,noOutputEQ=True,acousticFeedbackIncluded=False,audibleSustainMeasured=False,
        netWorkWindowMs=50,windowWorkNotGrossTransfer=True,sourceFrozenSha256=sha,pressureManifestSha256=ph,
        referenceManifestSha256=rh,maximumPartitionError=max(v['maximumPartitionError'] for v in cases))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'bridge_energy.json').write_text(json.dumps(dict(summary=summary,results=cases),indent=2,allow_nan=False))
    print('G3_BRIDGE_ENERGY_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()

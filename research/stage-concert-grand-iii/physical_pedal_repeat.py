"""G3.12r: dry physical-wire point dampers and repeatable shared hammers.
Rank-one dissipative contact per wire, hypothetical placement and strength.
Exact Woodbury midpoint; independent dense reference. No acoustic calibration."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from wire_physical_midpoint import CoupledWire,load
from physical_hammer_contact import Dense,Schur,Impact
from felt_law import params
from variable_damper import PedalControl
from split_radiation import relative

def damper_ports(a,rows,fraction=.18,width=.005):
    if not 0<fraction<1:raise ValueError('damper placement')
    B=np.zeros((a.n,a.nw));I=np.zeros((a.nw,a.partials,a.nw))
    for j,w in enumerate(a.wires):
        key=int(w.id.split('-')[0][1:]);L=rows[key]['lengthM']
        n=np.arange(1,len(w.w2)+1)
        if width>2*min(fraction,1-fraction)*L:raise ValueError('damper width')
        shape=np.sqrt(2/L)*np.sin(np.pi*n*fraction)*np.sinc(n*width/(2*L))
        B[:,j]=fraction*a.A[j];I[j,:,j]=w.U[:,:a.partials].T@shape
    return B,I

class PointSchur(Schur):
    def __init__(self,a,B,I):
        super().__init__(a);self.B=B;self.I=I
        self.V,self.U=super().solve(B,I)
        C=B.T@self.V+np.einsum('wip,wiq->pq',I,self.U)
        if relative(C,C.T)>1e-10 or np.linalg.eigvalsh((C+C.T)/2).min()<-1e-10*max(np.linalg.norm(C),1e-30):raise ValueError('damper compliance')
        self.C=(C+C.T)/2;self.loss=0.;self.set_levels(np.zeros(a.nw))
    def set_levels(self,d):
        self.d=np.asarray(d,float).copy()
        if self.d.shape!=(self.a.nw,) or not np.isfinite(self.d).all() or np.any(self.d<0):raise ValueError('damper coefficients')
        self.s=np.sqrt(self.d);self.small=cho_factor(np.eye(len(d))+(self.s[:,None]*self.C)*self.s)
    def solve(self,b,i):
        v,u=super().solve(b,i)
        y=self.B.T@v+np.einsum('wip,wiq->pq',self.I,u)
        t=self.s[:,None]*cho_solve(self.small,self.s[:,None]*y)
        return v-self.V@t,u-np.einsum('wip,pq->wiq',self.U,t)
    def step(self,F):
        a=self.a;h=self.h
        b,i=a.apply(a.v,a.u,a.Mb,a.mi,1.)
        g,j=a.apply(a.q,a.x,a.Kb,a.ki,a.ks)
        vm,um=self.solve((2*b/h-g+a.P@F)[:,None],(2*i/h-j+a.F@F)[:,:,None])
        v=vm[:,0];u=um[:,:,0]
        db,di=a.apply(v,u,a.Db,a.di,a.ds)
        intrinsic=h*float(v@db+np.sum(u*di))
        damper=self.B.T@v+np.einsum('wip,wi->p',self.I,u)
        extra=h*float(self.d@(damper*damper));self.loss+=extra
        obs=self.observe(v,u);work=h*float(F@obs)
        a.q+=h*v;a.x+=h*u;a.v=2*v-a.v;a.u=2*u-a.u
        return obs,work,intrinsic+extra

class PointDense(Dense):
    def __init__(self,a,B,I):
        super().__init__(a);self.Q=np.vstack([B,I.reshape(-1,a.nw)])
        self.baseD=self.D.copy();self.loss=0.;self.set_levels(np.zeros(a.nw))
    def set_levels(self,d):
        self.d=np.asarray(d,float).copy()
        if self.d.shape!=(self.a.nw,) or not np.isfinite(self.d).all() or np.any(self.d<0):raise ValueError('damper coefficients')
        self.D=self.baseD+(self.Q*self.d)@self.Q.T
        H=2*self.M/self.h+self.D+self.h*self.K/2
        self.fac=cho_factor(H*(self.s[:,None]*self.s[None,:]))
    def step(self,F):
        old=self.v.copy();o,w,l=super().step(F)
        mid=self.Q.T@((old+self.v)/2);self.loss+=self.h*float(self.d@(mid*mid))
        return o,w,l

class Repeating(Impact):
    def __init__(self,target,groups,masses,felts,reverse=False):
        super().__init__(target,groups,masses,felts,np.ones(len(masses)),reverse)
        self.v.fill(0.);self.x.fill(0.);self.active.fill(False)
        self.initial=0.;self.injected=0.;self.launches=0;self.captures=0;self.levels=None;self.rejected=0
    def launch(self,j,speed):
        if self.active[j]:
            self.rejected+=1;return False
        if not np.isfinite(speed) or speed<=0:raise ValueError('launch speed')
        self.x[j]=min(self.a.position()[self.group==j])-.0001
        self.v[j]=speed;self.active[j]=True;self.touched[j]=False
        self.injected+=.5*self.mass[j]*speed**2;self.launches+=1
        return True
    def damp(self,levels):
        if self.levels is not None and np.array_equal(levels,self.levels):return
        self.a.set_levels(levels);self.levels=levels.copy()
        C=self.a.compliance()
        if relative(C,C.T)>1e-10 or np.linalg.eigvalsh((C+C.T)/2).min()<-1e-10*max(np.linalg.norm(C),1e-30):raise ValueError('contact compliance')
        self.G=self.h*((C+C.T)/2+self.h/2*(self.B/self.mass)@self.B.T);self.cache.clear()
    def step(self):
        before=int(self.active.sum());out=super().step();self.captures+=before-int(self.active.sum())
        return out

def probe(k,D,A,wires,rows,groups,masses,felts,rate,n,pedal):
    ww=copy.deepcopy(wires);P=np.zeros((len(k),len(ww)))
    for i,w in enumerate(ww):w.port=i
    sa=CoupledWire(k,D,P,A,ww,rate,n);sb=CoupledWire(k,D,P,A,ww,rate,n)
    B,I=damper_ports(sa,rows)
    a=Repeating(PointSchur(sa,B,I),groups,masses,felts)
    b=Repeating(PointDense(sb,B,I),groups,masses,felts,True)
    ctrl=PedalControl(len(masses),rate,transition_ms=5.)
    group=np.asarray(groups);count=np.bincount(group);strength=2./count[group]
    events={}
    def event(t,kind,value):events.setdefault(round(t*rate),[]).append((kind,value))
    event(0.,'pedal',pedal)
    for j in range(len(masses)):
        for t in (0.,.030):
            event(t,'on',(j,[.5,1.,1.5,2.][j]))
        for t in (.010,.040):event(t,'off',j)
    event(.065,'pedal',0.)
    energy=state=force=peak=work=contact=0.;mismatch=0;before_release=None;memory=0.
    for t in range(round(.085*rate)):
        for kind,value in events.get(t,[]):
            if kind=='pedal':ctrl.sustain(value)
            elif kind=='off':ctrl.note(value,False)
            else:
                j,s=value;ctrl.note(j,True)
                memory=max(memory,float(a.z.max()))
                if a.launch(j,s)!=b.launch(j,s):raise ValueError('launch mismatch')
        if t==round(.065*rate):before_release=a.a.energy()
        levels=strength*ctrl.advance()[group]
        a.damp(levels);b.damp(levels)
        F,c,w,_=a.step();R,d,v,_=b.step()
        peak=max(peak,float(F.max()));force=max(force,float(np.max(abs(F-R))))
        contact=max(contact,c,d);work=max(work,w,v);mismatch+=int(not np.array_equal(a.active,b.active))
        q,u=a.a.state();qr,ur=b.a.state();dq=q-qr;dv=u-ur
        err=.5*float(dq@b.a.K@dq+dv@b.a.M@dv)
        state=max(state,np.sqrt(max(0.,err)/max(a.injected,1e-30)))
        for x in (a,b):
            energy=max(energy,abs(x.storage()+x.loss+x.feltloss+x.captureloss-x.injected)/max(x.injected,1e-30))
    result=dict(rate=rate,partials=n,pedal=pedal,launches=a.launches,captures=a.captures,rejected=a.rejected,
        captureMismatchSteps=mismatch,energyRelative=energy,stateEnergyRelative=state,forceRelative=force/max(peak,1e-30),
        contactResidualM=contact,workResidualJ=work,damperLossJ=a.a.loss,denseDamperLossJ=b.a.loss,
        damperLossRelative=abs(a.a.loss-b.a.loss)/max(a.injected,1e-30),energyBeforePedalReleaseJ=before_release,
        finalMechanicalEnergyJ=a.a.energy(),injectedJ=a.injected,retainedFeltMemoryM=memory)
    result['gate']=bool(a.launches==a.captures==2*len(masses) and a.rejected==0 and mismatch==0 and a.a.loss>0 and memory>0
        and max(energy,state,result['forceRelative'],result['damperLossRelative'])<=1e-8 and contact<=1e-12 and work<=1e-10)
    return result

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','hammer','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    raw=(a.hammer/'physical_hammer_contact.json').read_bytes();d=json.loads(raw);s=d['summary']
    if d['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in dict(gate=True,wires=10,structureRank=80,sharedHammerMass=True,individualFeltContacts=True,acousticLoadIncluded=False).items()):raise ValueError('unapproved hammer source')
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={r['key']:r for r in json.loads(a.scale.read_text())['rows']};keys=[45,48,60,64]
    pars=[params(k,rows[k]['count'],spec,felt) for k in keys];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    k,D,A=(z[x] for x in ('stiffness','damping','wirePorts'));cases=[]
    for rate in (48000,96000):
        for n in (16,32):
            for pedal in (0.,.5,1.):
                v=probe(k,D,A,wires,rows,groups,masses,felts,rate,n,pedal);cases.append(v)
                print('G3_PHYSICAL_PEDAL_CASE '+json.dumps(v,allow_nan=False),flush=True)
    # Pedal effect is a separate qualitative test, not a calibrated decay claim.
    trend=[]
    for rate in (48000,96000):
        for n in (16,32):
            x=[v['energyBeforePedalReleaseJ'] for v in cases if v['rate']==rate and v['partials']==n]
            trend.append(dict(rate=rate,partials=n,energiesJ=x,ordered=bool(x[0]<x[1]<x[2])))
    summary=dict(gate=all(v['gate'] for v in cases),pedalTrendGate=all(v['ordered'] for v in trend),diagnosticOnly=True,
        physicalHypothesis=True,calibratedParameters=False,structureRank=80,wires=10,keys=keys,damperPositionFraction=.18,
        damperWidthM=.005,damperMaximumPerNoteNsm=2.,transitionMs=5.,totalLaunches=sum(v['launches'] for v in cases),
        totalCaptures=sum(v['captures'] for v in cases),maximumEnergyError=max(v['energyRelative'] for v in cases),
        maximumStateError=max(v['stateEnergyRelative'] for v in cases),maximumForceError=max(v['forceRelative'] for v in cases),
        acousticLoadIncluded=False,timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'physical_pedal_repeat.json').write_text(json.dumps(dict(summary=summary,cases=cases,trend=trend,sourceFrozenSha256=sha,
        hammerManifestSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_PHYSICAL_PEDAL_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('physical pedal proof failed')
if __name__=='__main__':main()

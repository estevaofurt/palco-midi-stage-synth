"""G3.12k: individual wire felt contacts with one shared hammer per key.
Passive discrete-gradient felt law and exact midpoint compliance. Dry pilot."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from wire_physical_midpoint import CoupledWire,load
from compiled_wire_midpoint import Compiled
from felt_law import params,energy,relax,Felt
from compiled_contacts import ContactSolver
from multi_hammer_contact import solve_contacts
from split_radiation import relative

class Dense:
    def __init__(self,a):
        self.a=a;self.h=a.h;self.M,self.K,self.D,self.P=a.matrices()
        self.s=1/np.sqrt(np.diag(self.M))
        H=2*self.M/self.h+self.D+self.h*self.K/2
        self.fac=cho_factor(H*(self.s[:,None]*self.s[None,:]))
        self.q=np.zeros(len(H));self.v=self.q.copy()
    def solve(self,r):return self.s[:,None]*cho_solve(self.fac,self.s[:,None]*r) if r.ndim==2 else self.s*cho_solve(self.fac,self.s*r)
    def compliance(self):return self.P.T@self.solve(self.P)
    def position(self):return self.P.T@self.q
    def velocity(self):return self.P.T@self.v
    def free(self):return self.P.T@self.solve(2*self.M@self.v/self.h-self.K@self.q)
    def step(self,F):
        h=self.h;m=self.solve(2*self.M@self.v/h-self.K@self.q+self.P@F)
        self.q+=h*m;self.v=2*m-self.v;y=self.P.T@m
        return y,h*float(F@y),h*float(m@self.D@m)
    def energy(self):return .5*float(self.v@self.M@self.v+self.q@self.K@self.q)
    def state(self):return self.q,self.v

class Schur:
    def __init__(self,a):self.a=a;self.h=a.h
    def solve(self,b,i):
        a=self.a
        v=cho_solve(a.fac,b-a.A.T@np.sum(a.C[:,:,None]*i/a.Hi[:,:,None],axis=1))
        u=(i-a.C[:,:,None]*(a.A@v)[:,None,:])/a.Hi[:,:,None]
        return v,u
    def observe(self,b,i):return self.a.P.T@b+np.einsum('wip,wi->p',self.a.F,i)
    def compliance(self):
        a=self.a;v,u=self.solve(a.P,a.F)
        return a.P.T@v+np.einsum('wip,wiq->pq',a.F,u)
    def position(self):return self.observe(self.a.q,self.a.x)
    def velocity(self):return self.observe(self.a.v,self.a.u)
    def free(self):
        a=self.a;b,i=a.apply(a.v,a.u,a.Mb,a.mi,1.)
        g,j=a.apply(a.q,a.x,a.Kb,a.ki,a.ks)
        v,u=self.solve((2*b/a.h-g)[:,None],(2*i/a.h-j)[:,:,None])
        return self.observe(v[:,0],u[:,:,0])
    def step(self,F):return self.a.step(F)
    def energy(self):return self.a.energy()
    def state(self):return np.r_[self.a.q,self.a.x.ravel()],np.r_[self.a.v,self.a.u.ravel()]

class Impact:
    def __init__(self,target,groups,masses,felts,speeds,reverse=False):
        self.a=target;self.h=target.h;self.group=np.asarray(groups,int);self.mass=np.asarray(masses,float)
        self.felts=tuple(felts);self.reverse=reverse;self.v=np.asarray(speeds,float).copy()
        n=len(self.group);nh=len(self.mass)
        if len(self.felts)!=n or len(self.v)!=nh or set(self.group)!=set(range(nh)) or min(self.mass)<=0 or min(self.v)<=0:raise ValueError('contact dimensions')
        # Identical initial gap for wires struck by a single hammer.
        y=target.position();self.x=np.array([min(y[self.group==j])-.0001 for j in range(nh)])
        self.z=np.zeros(n);self.active=np.ones(nh,bool);self.touched=np.zeros(nh,bool)
        self.B=np.eye(nh)[self.group];C=target.compliance()
        if relative(C,C.T)>1e-10 or np.linalg.eigvalsh((C+C.T)/2).min()<-1e-10*max(np.linalg.norm(C),1e-30):raise ValueError('invalid mechanical compliance')
        self.G=self.h*((C+C.T)/2+self.h/2*(self.B/self.mass)@self.B.T)
        self.loss=self.feltloss=self.captureloss=0.;self.initial=self.storage();self.cache={}
    def compression(self):return np.where(self.active[self.group],self.x[self.group]-self.a.position(),0.)
    def storage(self):
        return self.a.energy()+.5*float(self.mass@(self.v*self.v))+sum(energy(d,z,f) for d,z,f in zip(self.compression(),self.z,self.felts))
    def step(self):
        h=self.h;d0=self.compression();ids=np.flatnonzero(self.active[self.group])
        F=np.zeros(len(self.group));err=workerr=0.;sweeps=0
        for i in np.flatnonzero(~self.active[self.group]):
            f=self.felts[i];old=self.z[i];k=h*f.kr/(2*f.eta)
            if k>1:raise ValueError('recovery bound')
            self.z[i]=old*(1-k)/(1+k);self.feltloss+=f.eta*(old-self.z[i])**2/h
        if len(ids):
            first=[relax(d0[i],self.z[i],h/2,self.felts[i]) for i in ids]
            z=np.array([v[0] for v in first]);free=d0[ids]+h*(self.v[self.group[ids]]-self.a.free()[ids])
            G=self.G[np.ix_(ids,ids)];felts=[self.felts[i] for i in ids]
            if self.reverse:f,sweeps,_=solve_contacts(d0[ids],free,z,G,felts,True,400)
            else:
                key=tuple(ids)
                if key not in self.cache:self.cache[key]=ContactSolver(G,felts)
                f,sweeps,_=self.cache[key].solve(np.ascontiguousarray(d0[ids]),np.ascontiguousarray(free),z)
            F[ids]=f;expected=free-G@f
            total=self.B.T@F;dx=h*self.v-h*h*total/(2*self.mass)
            _,work,loss=self.a.step(F);self.x+=dx;self.v-=h*total/self.mass
            d1=self.compression();err=float(np.max(abs(d1[ids]-expected)))
            workerr=abs(work-float(F@(dx[self.group]-(d1-d0))))
            second=[relax(d1[i],v,h/2,self.felts[i]) for i,v in zip(ids,z)]
            self.z[ids]=[v[0] for v in second];self.feltloss+=sum(v[1] for v in first+second)
            self.touched|=total>0;vel=self.a.velocity()
            for j in np.flatnonzero(self.active):
                mask=self.group==j
                if self.touched[j] and self.v[j]<0 and np.all(d1[mask]<=0) and np.all(self.v[j]-vel[mask]<=0):
                    self.captureloss+=.5*self.mass[j]*self.v[j]**2;self.v[j]=0.;self.active[j]=False
        else:_,work,loss=self.a.step(F)
        self.loss+=loss
        if min(loss,float(F.min()))<-1e-14:raise ValueError('nonpassive step')
        return F,err,workerr,sweeps

def probe(k,D,A,wires,groups,masses,felts,rate,n,speeds,duration=.035):
    # Each wire now has its own conjugate force port; do not use the
    # previous aggregate hammer ports (which would multiply force).
    P=np.zeros((len(k),len(wires)));ww=copy.deepcopy(wires)
    for i,w in enumerate(ww):w.port=i
    a=Impact(Schur(Compiled(k,D,P,A,ww,rate,n)),groups,masses,felts,speeds)
    b=Impact(Dense(CoupledWire(k,D,P,A,ww,rate,n)),groups,masses,felts,speeds,True)
    balance=state=force=peak=contact=work=0.;sweeps=0;concurrent=0;counts=np.zeros(len(ww),int)
    peaks=np.zeros(len(ww));mismatch=0
    for t in range(round(duration*rate)):
        F,c,w,s=a.step();R,d,v,j=b.step()
        peaks=np.maximum(peaks,F);counts+=F>0;peak=max(peak,float(F.max()))
        force=max(force,float(np.max(abs(F-R))));concurrent=max(concurrent,int(np.count_nonzero(F)))
        contact=max(contact,c,d);work=max(work,w,v);sweeps=max(sweeps,s,j)
        q,u=a.a.state();qr,ur=b.a.state()
        state=max(state,relative(q,qr),relative(u,ur))
        balance=max(balance,abs(a.storage()+a.loss+a.feltloss+a.captureloss-a.initial)/a.initial,
            abs(b.storage()+b.loss+b.feltloss+b.captureloss-b.initial)/b.initial)
        mismatch+=int(not np.array_equal(a.active,b.active))
    captured=int((~a.active).sum());nh=len(masses)
    result=dict(rate=rate,partials=n,hammers=nh,wires=len(ww),speedsMps=list(speeds),captured=captured,
        maximumConcurrentContacts=concurrent,peakForcesN=peaks.tolist(),contactDurationsMs=(1000*counts/rate).tolist(),
        energyRelative=balance,stateRelative=state,forceRelative=force/max(peak,1e-30),maximumSweeps=sweeps,
        contactResidualM=contact,workResidualJ=work,captureMismatchSteps=mismatch,
        initialEnergyJ=a.initial,targetEnergyJ=a.a.energy(),feltLossJ=a.feltloss,captureLossJ=a.captureloss,mechanicalLossJ=a.loss)
    result['gate']=bool(captured==nh and mismatch==0 and np.all(peaks>0) and a.feltloss>0 and a.a.energy()>0
        and max(balance,state,result['forceRelative'])<=1e-8 and contact<=1e-12 and work<=1e-10)
    return result

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','compiled','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    raw=(a.compiled/'compiled_wire_midpoint.json').read_bytes();d=json.loads(raw);s=d['summary']
    if d['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in dict(gate=True,structureRank=80,wires=10,acousticLoadIncluded=False,hammerContactIncluded=False,timeDomainReady=False).items()):raise ValueError('unapproved compiled source')
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']};keys=[45,48,60,64]
    pars=[params(k,rows[k]['count'],spec,felt) for k in keys]
    masses=[h['massKg'] for h,_ in pars];groups=[w.port for w in wires];felts=[pars[g][1] for g in groups]
    k,D,A=(z[x] for x in ('stiffness','damping','wirePorts'))
    cases=[]
    for r in (48000,96000):
        for n in (16,32):
            for speed in ([.3,.5,.7,1.],[1.,1.5,2.,3.]):
                v=probe(k,D,A,wires,groups,masses,felts,r,n,speed);cases.append(v)
                print('G3_PHYSICAL_HAMMER_CASE '+json.dumps(v,allow_nan=False),flush=True)
    summary=dict(gate=all(v['gate'] for v in cases),diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,
        structureRank=80,keys=keys,wires=10,sharedHammerMass=True,individualFeltContacts=True,
        maximumEnergyError=max(v['energyRelative'] for v in cases),maximumStateError=max(v['stateRelative'] for v in cases),
        maximumForceError=max(v['forceRelative'] for v in cases),maximumSweeps=max(v['maximumSweeps'] for v in cases),
        totalCaptures=sum(v['captured'] for v in cases),acousticLoadIncluded=False,midiCalibration=False,
        timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'physical_hammer_contact.json').write_text(json.dumps(dict(summary=summary,cases=cases,
        sourceFrozenSha256=sha,compiledManifestSha256=hashlib.sha256(raw).hexdigest(),hammerMassesKg=masses,
        feltPerWire=[f.__dict__ for f in felts]),indent=2,allow_nan=False))
    print('G3_PHYSICAL_HAMMER_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('physical hammer diagnostic failed')
if __name__=='__main__':main()

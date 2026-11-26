"""G3.11s: event-driven individual hammer capture and repeat.
Synthetic proof only, fixed damping during each run. Not a MIDI/audio engine."""
import argparse,json
from pathlib import Path
import numpy as np
from felt_law import energy,relax
from multi_hammer_contact import make,solve_contacts
from coupled_hammer_contact import midpoint
from compiled_contacts import ContactSolver
from compiled_string_board import state_error

class HammerBank:
    def __init__(self,n,partials,rate,solver='schur'):
        a=make(n,partials,rate,solver)
        self.a=a.a;self.P=a.P;self.m=a.m;self.G=a.G;self.felts=a.felts
        self.x=np.zeros(n);self.v=np.zeros(n);self.z=np.zeros(n)
        self.active=np.zeros(n,dtype=bool);self.touched=self.active.copy()
        self.Fb=a.Fb;self.Fs=a.Fs;self.h=self.a.h;self.mode=solver
        self.loss=self.feltloss=self.captureloss=self.injected=0.
        self.launches=np.zeros(n,dtype=int);self.captures=self.launches.copy()
        self.cached_key=None;self.cached=None
        self.solves=self.idle_steps=0
    def compression(self):
        d=self.x-self.P.T@self.a.q
        return np.where(self.active,d,0.)
    def storage(self):
        return self.a.energy()+.5*float(np.sum(self.m*self.v**2))+sum(energy(d,z,f) for d,z,f in zip(self.compression(),self.z,self.felts))
    def launch(self,i,speed,gap=1e-4):
        if type(i)!=int or not 0<=i<len(self.m) or self.active[i] or not np.isfinite([speed,gap]).all() or speed<=0 or gap<0:
            raise ValueError('invalid launch or hammer not captured')
        self.x[i]=float(self.P[:,i]@self.a.q)-gap
        self.v[i]=speed;self.active[i]=True;self.touched[i]=False
        self.injected+=.5*self.m[i]*speed**2;self.launches[i]+=1
        # z deliberately persists across strikes.
    def step(self):
        a=self.a;h=self.h;d0=self.compression()
        # Open/captured felt has only its recovery spring energy. Its implicit
        # midpoint recovery is exact for this linear subproblem.
        z0=self.z.copy();ids=np.flatnonzero(self.active);inactive=~self.active
        for i in np.flatnonzero(inactive):
            f=self.felts[i];k=h*f.kr/(2*f.eta)
            if k>1:raise ValueError('recovery timestep too large')
            self.z[i]=z0[i]*(1-k)/(1+k)
            self.feltloss+=f.eta*(self.z[i]-z0[i])**2/h
        F=np.zeros(len(self.m));residual=0.;sweeps=0;contact_error=0.;work_error=0.
        if len(ids):
            first=[relax(d0[i],self.z[i],h/2,self.felts[i]) for i in ids]
            z=np.array([v[0] for v in first])
            _,sm=midpoint(a,self.Fb,self.Fs)
            dfree=d0[ids]+h*(self.v[ids]-self.P[:,ids].T@sm)
            G=self.G[np.ix_(ids,ids)];felts=[self.felts[i] for i in ids]
            if self.mode=='schur':
                key=tuple(ids)
                if key!=self.cached_key:self.cached=ContactSolver(G,felts);self.cached_key=key
                f,sweeps,residual=self.cached.solve(np.ascontiguousarray(d0[ids]),np.ascontiguousarray(dfree),z)
            else:f,sweeps,residual=solve_contacts(d0[ids],dfree,z,G,felts,True,400)
            F[ids]=f;self.solves+=1;expected=dfree-G@f
            dx=h*self.v[ids]-h*h*f/(2*self.m[ids])
            w=a.step(self.Fb,self.P@F)
            self.x[ids]+=dx;self.v[ids]-=h*f/self.m[ids]
            d1=self.compression()
            second=[relax(d1[i],v,h/2,self.felts[i]) for i,v in zip(ids,z)]
            self.z[ids]=[v[0] for v in second]
            self.feltloss+=sum(v[1] for v in first+second)
            self.touched[ids]|=f>0
            contact_error=float(np.max(np.abs(d1[ids]-expected)))
            work_error=abs(w[0]-float(f@(dx-(d1[ids]-d0[ids]))))
            # Capture at an open, receding contact. Remove kinetic energy
            # into a separate catcher loss; no spring potential is removed.
            for i in ids:
                if self.touched[i] and d1[i]<=0 and self.v[i]<0 and self.v[i]-self.P[:,i]@a.v<=0:
                    self.captureloss+=.5*self.m[i]*self.v[i]**2
                    self.v[i]=0.;self.active[i]=False;self.captures[i]+=1
        else:
            w=a.step(self.Fb,self.Fs);self.idle_steps+=1
        self.loss+=float(w[1:].sum())
        if not np.isfinite([self.storage(),self.loss,self.feltloss,self.captureloss]).all() or min(float(F.min()),float(w[1:].min()))<-1e-14:raise ValueError('invalid hammer state')
        return F,dict(sweeps=sweeps,residual=residual,contactError=contact_error,workError=work_error)

def probe(n,partials,rate):
    a=HammerBank(n,partials,rate);b=HammerBank(n,partials,rate,'dense')
    # Three staggered attacks per hammer. Repeat only after all are captured;
    # record actual inter-strike timing, never reset string or felt states.
    start=0;rounds=0;next_launch=0;peak=0.;error=state=force=work=contact=0.;active_peak=0;memory=0.;rejected=0
    events=[];schedule=[];i=0
    for i in range(round(.12*rate)):
        if rounds<3 and not schedule and not a.active.any() and not b.active.any() and i>=next_launch:
            schedule=[(i+round(j*.00017*rate),j,float([.3,1.,3.][(j+rounds)%3])) for j in range(n)]
            rounds+=1
        while schedule and schedule[0][0]<=i:
            _,j,speed=schedule.pop(0);memory=max(memory,float(a.z[j]))
            before=a.storage();a.launch(j,speed);b.launch(j,speed)
            error=max(error,abs(a.storage()-before-.5*a.m[j]*speed**2))
            events.append(dict(sample=i,hammer=j,speedMps=speed))
            next_launch=i+round(.012*rate)
            if not rejected:
                try:a.launch(j,speed)
                except ValueError:rejected+=1
        F,r=a.step();G,s=b.step()
        peak=max(peak,float(F.max()));force=max(force,float(np.max(np.abs(F-G))))
        state=max(state,state_error(a.a,b.a));work=max(work,r['workError'],s['workError'])
        contact=max(contact,r['contactError'],s['contactError']);active_peak=max(active_peak,int(a.active.sum()))
        error=max(error,abs(a.storage()+a.loss+a.feltloss+a.captureloss-a.injected),
                        abs(b.storage()+b.loss+b.feltloss+b.captureloss-b.injected))
        if not np.array_equal(a.active,b.active):raise ValueError('capture timing mismatch')
        if rounds==3 and not schedule and not a.active.any() and i>=next_launch:break
    energy_error=error/max(a.injected,1e-30);force_error=force/max(peak,1e-30)
    gate=bool(np.all(a.launches==3) and np.all(a.captures==3) and np.array_equal(a.captures,b.captures)
        and a.idle_steps>0 and a.captureloss>0 and memory>0 and rejected==1 and energy_error<=1e-8
        and max(state,force_error)<=1e-8 and work<=1e-10 and contact<=1e-12)
    return dict(hammers=n,partials=partials,sampleRate=rate,launches=int(a.launches.sum()),captures=int(a.captures.sum()),
        activePeak=active_peak,contactSolveSteps=a.solves,idleSteps=a.idle_steps,simulatedSamples=i+1,
        retainedFeltMemoryM=memory,captureLossJ=a.captureloss,energyRelative=energy_error,stateRelative=state,
        forceRelative=force_error,workResidualJ=work,contactResidualM=contact,events=events,gate=gate)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[probe(n,j,r) for n in (2,4,8) for j in (4,8) for r in (48000,96000)]
    gate=all(v['gate'] for v in rows)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,maximumHammers=8,
        maximumEnergyError=max(v['energyRelative'] for v in rows),maximumStateError=max(v['stateRelative'] for v in rows),
        maximumForceError=max(v['forceRelative'] for v in rows),totalLaunches=sum(v['launches'] for v in rows),
        totalCaptures=sum(v['captures'] for v in rows),totalIdleSteps=sum(v['idleSteps'] for v in rows),
        physicalFitAccepted=False,timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'hammer_lifecycle.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_HAMMER_LIFECYCLE_GATE '+json.dumps(summary),flush=True)
    for v in rows:print('G3_HAMMER_LIFECYCLE_CASE '+json.dumps({k:x for k,x in v.items() if k!='events'}),flush=True)
    if not gate:raise ValueError('hammer lifecycle diagnostic failed')
if __name__=='__main__':main()

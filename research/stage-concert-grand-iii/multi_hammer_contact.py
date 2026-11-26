"""G3.11q: simultaneous unilateral felt contacts on shared passive structure.
Fixed linear target, synthetic parameters; no event engine or audio rendering."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from felt_law import Felt,energy,relax,frozen_force
from coupled_hammer_contact import midpoint
from compiled_string_board import fixture,state_error

def solve_contacts(d0,dfree,z,G,felts,reverse=False,max_sweeps=80):
    """Coordinate root solve of F=frozen_force(d0,dfree-G F,z).
    The SPD compliance is verified on construction; signed off-diagonals
    are retained. Every coordinate has a monotone scalar equation."""
    n=len(d0);F=np.zeros(n);order=range(n-1,-1,-1) if reverse else range(n)
    for sweep in range(1,max_sweeps+1):
        for j in order:
            free=dfree[j]-G[j]@F+G[j,j]*F[j]
            hi=frozen_force(d0[j],free,z[j],felts[j])
            if hi<=0:F[j]=0.;continue
            def fun(v):return v-frozen_force(d0[j],free-G[j,j]*v,z[j],felts[j])
            F[j]=brentq(fun,0.,hi,xtol=1e-13) if fun(hi)>0 else hi
        d1=dfree-G@F
        expected=np.array([frozen_force(a,b,c,f) for a,b,c,f in zip(d0,d1,z,felts)])
        error=float(np.max(np.abs(F-expected)))
        if error<=1e-11*max(1.,float(np.max(F))):return F,sweep,error
    raise ValueError('simultaneous contact residual not converged')

class MultiImpact:
    def __init__(self,a,ports,mass,speeds,felts,reverse=False):
        self.a=a;self.P=np.asarray(ports,dtype=float).copy();self.m=np.asarray(mass,dtype=float).copy()
        self.v=np.asarray(speeds,dtype=float).copy();self.felts=tuple(felts);self.reverse=reverse
        n=len(self.m)
        if not n or self.P.shape!=(len(a.q),n) or self.v.shape!=(n,) or len(self.felts)!=n or not all(np.isfinite(v).all() for v in (self.P,self.m,self.v)) or np.any(self.m<=0) or np.any(self.v<=0) or np.any(np.linalg.norm(self.P,axis=0)==0):raise ValueError('invalid simultaneous hammer parameters')
        self.x=self.P.T@a.q;self.z=np.zeros(n);self.Fb=np.zeros_like(a.b.q);self.Fs=np.zeros_like(a.q)
        response=np.column_stack([midpoint(a,self.Fb,self.P[:,j],True)[1] for j in range(n)])
        C=self.P.T@response
        if np.linalg.norm(C-C.T)>1e-10*max(np.linalg.norm(C),1e-30) or np.linalg.eigvalsh((C+C.T)/2).min()<-1e-10*max(np.linalg.norm(C),1e-30):raise ValueError('nonreciprocal contact compliance')
        self.C=C;self.G=a.h*((C+C.T)/2+np.diag(a.h/(2*self.m)))
        if np.linalg.eigvalsh(self.G).min()<=0:raise ValueError('nonpositive contact compliance')
        self.loss=0.;self.feltloss=0.;self.impulse=np.zeros(n)
    def compression(self):return self.x-self.P.T@self.a.q
    def storage(self):
        return self.a.energy()+.5*float(np.sum(self.m*self.v**2))+sum(energy(d,z,f) for d,z,f in zip(self.compression(),self.z,self.felts))
    def step(self):
        a=self.a;h=a.h;d0=self.compression()
        first=[relax(d,z,h/2,f) for d,z,f in zip(d0,self.z,self.felts)]
        z=np.array([v[0] for v in first])
        _,sm=midpoint(a,self.Fb,self.Fs)
        dfree=d0+h*(self.v-self.P.T@sm)
        F,sweeps,residual=solve_contacts(d0,dfree,z,self.G,self.felts,self.reverse)
        expected=dfree-self.G@F
        dx=h*self.v-h*h*F/(2*self.m)
        w=a.step(self.Fb,self.P@F)
        self.x+=dx;self.v-=h*F/self.m;d1=self.compression()
        second=[relax(d,v,h/2,f) for d,v,f in zip(d1,z,self.felts)]
        self.z=np.array([v[0] for v in second])
        self.loss+=float(w[1:].sum());self.feltloss+=sum(v[1] for v in first+second);self.impulse+=h*F
        if not all(np.isfinite(v).all() for v in (F,d1,self.v,self.z,w)) or min(float(F.min()),float(w[1:].min()),*(v[1] for v in first+second))<-1e-14:raise ValueError('invalid contact')
        return F,dict(sweeps=sweeps,forceResidual=residual,contactResidual=float(np.max(np.abs(d1-expected))),
            workResidual=abs(w[0]-float(F@(dx-(d1-d0)))),relaxResidual=max(abs(v[2]) for v in first+second))

def make(n,partials,rate,solver,reverse=False):
    a=fixture(n,partials,32,5,rate,solver)
    P=np.zeros((n*partials,n))
    for j in range(n):
        P[j*partials:(j+1)*partials,j]=np.sin(np.pi*(.13+.04*(j%3))*np.arange(1,partials+1))/np.sqrt(partials)
    speeds=np.resize(np.array([.3,1.,3.,.7]),n)
    return MultiImpact(a,P,np.full(n,.01),speeds,[Felt(1.5e8,.5e8,3000.,3.,2.5)]*n,reverse)

def probe(n,partials,rate):
    a=make(n,partials,rate,'schur');b=make(n,partials,rate,'dense',True)
    E0=a.storage();v0=a.v.copy();peak=np.zeros(n);count=np.zeros(n,dtype=int);started=np.zeros(n,dtype=bool)
    balance=state=forceerr=contact=work=relaxerr=residual=0.;sweeps=0;separated=False;simultaneous=0
    for i in range(round(.04*rate)):
        F,r=a.step();G,s=b.step()
        peak=np.maximum(peak,F);count+=F>0;started|=F>0;simultaneous=max(simultaneous,int(np.count_nonzero(F)))
        balance=max(balance,abs(a.storage()+a.loss+a.feltloss-E0))
        state=max(state,state_error(a.a,b.a))
        forceerr=max(forceerr,float(np.max(np.abs(F-G))))
        contact=max(contact,r['contactResidual'],s['contactResidual'])
        work=max(work,r['workResidual'],s['workResidual'])
        relaxerr=max(relaxerr,r['relaxResidual'],s['relaxResidual'])
        residual=max(residual,r['forceResidual'],s['forceResidual']);sweeps=max(sweeps,r['sweeps'],s['sweeps'])
        if np.all(started) and np.all(a.compression()<=0) and np.all(a.v<0) and np.all(a.v-a.P.T@a.a.v<=0):
            separated=True;break
    impulse=float(np.max(np.abs(a.m*(v0-a.v)-a.impulse)))
    result=dict(hammers=n,partials=partials,sampleRate=rate,separated=separated,maximumConcurrentContacts=simultaneous,
        peakForces=peak.tolist(),contactDurationsMs=(1000*count/rate).tolist(),reboundMps=(-a.v).tolist(),
        targetEnergy=a.a.energy(),feltLoss=a.feltloss,energyRelative=balance/E0,stateRelative=state,
        forceRelative=forceerr/max(float(peak.max()),1e-30),forceResidualN=residual,maximumSweeps=sweeps,
        contactResidualM=contact,workResidualJ=work,relaxResidualJ=relaxerr,impulseResidual=impulse,
        crossComplianceRelative=float(np.linalg.norm(a.C-np.diag(np.diag(a.C)))/max(np.linalg.norm(a.C),1e-30)))
    result['gate']=bool(separated and simultaneous==n and np.all(peak>0) and a.feltloss>0 and a.a.energy()>0 and result['energyRelative']<=1e-8
        and max(state,result['forceRelative'])<=1e-8 and contact<=1e-12 and work<=1e-10 and relaxerr<=1e-11 and impulse<=1e-10)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[probe(n,j,r) for n in (2,4,8) for j in (4,8) for r in (48000,96000)]
    gate=all(v['gate'] for v in rows)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,maximumHammers=8,maximumEnergyError=max(v['energyRelative'] for v in rows),
        maximumStateError=max(v['stateRelative'] for v in rows),maximumForceError=max(v['forceRelative'] for v in rows),
        maximumSweeps=max(v['maximumSweeps'] for v in rows),physicalFitAccepted=False,timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'multi_hammer_contact.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_MULTI_HAMMER_GATE '+json.dumps(summary),flush=True)
    for v in rows:print('G3_MULTI_HAMMER_CASE '+json.dumps(v),flush=True)
    if not gate:raise ValueError('multi-hammer diagnostic failed')
if __name__=='__main__':main()

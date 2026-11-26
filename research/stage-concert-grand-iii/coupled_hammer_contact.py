"""G3.11p: single hammer contact with the coupled string-board-air model.
Reuse the passive internal-variable felt law; synthetic parameters only.
First separation ends the diagnostic; no action/catcher or multi-hammer MIDI."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_solve
from scipy.optimize import brentq
from felt_law import Felt,energy,relax,frozen_force
from compiled_string_board import fixture,state_error
from split_radiation import relative

def midpoint(a,Fb,Fs,homogeneous=False):
    """Read-only midpoint response, independently assembled for dense path.
    homogeneous=True computes force compliance, not an advancing step."""
    b=a.b;h=a.h
    if homogeneous:
        air=np.zeros(b.A.shape[0]);rel=np.zeros_like(a.q)
        vb=np.zeros_like(b.v);qb=np.zeros_like(b.q);vs=np.zeros_like(a.v);qs=np.zeros_like(a.q)
    else:
        u=b.A@b.v;z=b.A@b.q;rel=a.q-a.G@z
        free=(b.a-h*b.om2*b.x/2)/b.den
        air=2*b.M@u/h-b.K@z-np.einsum('jik,jk->i',b.B,free)
        vb,qb,vs,qs=b.v,b.q,a.v,a.q
    if a.solver=='schur':
        rs=2*a.ms*vs/h-a.ks*qs+Fs-a.kc*rel
        g=a.G.T@(a.kc*rel+a.c*rs/a.hs)
        rhs=2*b.m*vb/h-b.k*qb+Fb+b.A.T@(air+g)
        y=rhs/b.diag;vm=y-a.V@cho_solve(a.fac,a.U.T@y)
        sm=(rs+a.c*(a.G@(b.A@vm)))/a.hs
    else:
        rhs=2*a.M0@np.r_[vb,vs]/h-a.K0@np.r_[qb,qs]+np.r_[Fb,Fs]+a.Aug.T@air
        v=cho_solve(a.fac,rhs);vm=v[:len(b.m)];sm=v[len(b.m):]
    return vm,sm

class Impact:
    def __init__(self,a,port,mass,speed,felt):
        self.a=a;self.port=np.asarray(port,dtype=float).copy();self.m=float(mass);self.v=float(speed);self.x=0.;self.z=0.;self.felt=felt
        if self.port.shape!=a.q.shape or not np.isfinite(self.port).all() or not np.any(self.port) or not np.isfinite([mass,speed]).all() or min(mass,speed)<=0:raise ValueError('invalid hammer')
        self.Fb=np.zeros_like(a.b.q);self.Fs=np.zeros_like(a.q)
        _,response=midpoint(a,self.Fb,self.port,True)
        self.compliance=float(self.port@response)
        if self.compliance<0 or not np.isfinite(self.compliance):raise ValueError('nonpassive contact compliance')
        self.g=a.h*(a.h/(2*self.m)+self.compliance)
        self.loss=0.;self.feltloss=0.;self.impulse=0.
    def compression(self):
        return self.x-float(self.port@self.a.q)
    def storage(self):
        return self.a.energy()+.5*self.m*self.v**2+energy(self.compression(),self.z,self.felt)
    def step(self):
        a=self.a;h=a.h;f=self.felt;d0=self.compression()
        z,l0,e0=relax(d0,self.z,h/2,f)
        _,sm=midpoint(a,self.Fb,self.Fs)
        dfree=d0+h*(self.v-self.port@sm)
        hi=frozen_force(d0,dfree,z,f)
        def residual(F):
            return F-frozen_force(d0,dfree-self.g*F,z,f)
        F=brentq(residual,0.,hi,xtol=1e-13) if hi>0 and residual(hi)>0 else hi
        expected=dfree-self.g*F
        w=a.step(self.Fb,F*self.port)
        self.x+=h*self.v-h*h*F/(2*self.m);self.v-=h*F/self.m
        d1=self.compression()
        self.z,l1,e1=relax(d1,z,h/2,f)
        self.loss+=float(w[1:].sum());self.feltloss+=l0+l1;self.impulse+=h*F
        if not np.isfinite([F,d1,self.v,self.loss,self.feltloss]).all() or min(F,l0,l1,*w[1:])<-1e-14:raise ValueError('invalid contact')
        return dict(force=F,compression=d1,contactResidual=abs(d1-expected),relaxResidual=max(abs(e0),abs(e1)),
            workResidual=abs(w[0]-F*(h*self.v+h*h*F/(2*self.m)-(d1-d0))))

def make(rate,speed,partials,solver):
    a=fixture(4,partials,32,5,rate,solver)
    port=np.zeros_like(a.q);port[:partials]=np.sin(np.pi*.17*np.arange(1,partials+1))/np.sqrt(partials)
    return Impact(a,port,.01,speed,Felt(1.5e8,.5e8,3000.,3.,2.5))

def probe(rate,speed,partials):
    a=make(rate,speed,partials,'schur');b=make(rate,speed,partials,'dense')
    E0=a.storage();peak=depth=err=state=forceerr=contact=relaxerr=workerr=0.;count=0;started=False;separated=False
    for i in range(round(.04*rate)):
        x=a.step();y=b.step();F=x['force'];peak=max(peak,F);depth=max(depth,x['compression'])
        if F>0:started=True;count+=1
        err=max(err,abs(a.storage()+a.loss+a.feltloss-E0))
        state=max(state,state_error(a.a,b.a));forceerr=max(forceerr,abs(F-y['force']))
        contact=max(contact,x['contactResidual']);relaxerr=max(relaxerr,x['relaxResidual']);workerr=max(workerr,x['workResidual'])
        if started and x['compression']<=0 and a.v<0 and a.v-a.port@a.a.v<=0:
            separated=True;break
    impulse=abs(a.m*(speed-a.v)-a.impulse)
    result=dict(sampleRate=rate,speedMps=speed,partials=partials,initialEnergy=E0,targetEnergy=a.a.energy(),
        hammerReboundEnergy=.5*a.m*a.v**2,feltStoredEnergy=energy(a.compression(),a.z,a.felt),feltLoss=a.feltloss,structuralAndAcousticLoss=a.loss,
        peakForce=peak,maximumCompression=depth,contactDurationMs=1000*count/rate,reboundMps=-a.v,separated=separated,
        energyRelative=err/E0,stateRelative=state,forceRelative=forceerr/max(peak,1e-30),contactResidualM=contact,
        feltRelaxResidualJ=relaxerr,workResidualJ=workerr,impulseResidual=impulse)
    result['gate']=bool(separated and peak>0 and depth>0 and a.feltloss>0 and a.a.energy()>0 and err/E0<=1e-8 and state<=1e-8
        and result['forceRelative']<=1e-8 and contact<=1e-12 and relaxerr<=1e-11 and workerr<=1e-10 and impulse<=1e-10)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[probe(r,v,j) for r in (48000,96000,192000) for v in (.3,1.,3.) for j in (4,8)]
    comparisons=[]
    for v in (.3,1.,3.):
        for j in (4,8):
            lo,hi=[next(x for x in rows if x['sampleRate']==r and x['speedMps']==v and x['partials']==j) for r in (96000,192000)]
            errors={k:abs(lo[k]-hi[k])/max(abs(hi[k]),1e-30) for k in ('peakForce','maximumCompression','targetEnergy','reboundMps','feltLoss')}
            dt=abs(lo['contactDurationMs']-hi['contactDurationMs'])
            comparisons.append(dict(speedMps=v,partials=j,relative=errors,durationDeltaMs=dt,gate=bool(max(errors.values())<=.05 and dt<=.1)))
    gate=all(x['gate'] for x in rows)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,existingFeltLaw=True,maximumEnergyError=max(x['energyRelative'] for x in rows),
        maximumStateError=max(x['stateRelative'] for x in rows),maximumForceError=max(x['forceRelative'] for x in rows),
        sampleRateConvergenceGate=all(x['gate'] for x in comparisons),physicalFitAccepted=False,timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'coupled_hammer_contact.json').write_text(json.dumps(dict(summary=summary,cases=rows,convergence=comparisons),indent=2,allow_nan=False))
    print('G3_HAMMER_COUPLED_GATE '+json.dumps(summary),flush=True)
    for row in rows:print('G3_HAMMER_COUPLED_CASE '+json.dumps(row),flush=True)
    if not gate:raise ValueError('hammer contact diagnostic failed')
if __name__=='__main__':main()

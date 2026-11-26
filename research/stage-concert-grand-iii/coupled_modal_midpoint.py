"""G3.11i: reciprocal implicit midpoint coupling with a low-rank board load.
Synthetic structural/air parameters only. No rejected physical fit is used."""
import argparse,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from passive_midpoint import factor_psd
from split_radiation import relative

class CoupledModal:
    def __init__(self,m,k,d,A,C,centers,gamma_hz,rate,solver='lowrank'):
        m,k,d,A,C=map(np.asarray,(m,k,d,A,C));centers=np.asarray(centers,float)
        n=len(m)
        if any(np.iscomplexobj(x) or not np.isfinite(x).all() for x in (m,k,d,A,C,centers)) or m.shape!=(n,) or k.shape!=(n,) or d.shape!=(n,) or np.any(m<=0) or np.any(k<0) or np.any(d<0):raise ValueError('invalid structural coefficients')
        if A.ndim!=2 or A.shape[1]!=n or C.shape!=(len(centers)+3,A.shape[0],A.shape[0]) or not len(centers) or np.any(centers<=0) or not np.isfinite([gamma_hz,rate]).all() or min(gamma_hz,rate)<=0 or solver not in ('dense','lowrank'):raise ValueError('invalid acoustic coefficients')
        self.m,self.k,self.d,self.A=m.copy(),k.copy(),d.copy(),A.copy()
        self.h=h=1/rate;self.gamma=2*np.pi*gamma_hz;self.om2=(2*np.pi*centers[:,None])**2
        B=[factor_psd(x) for x in C];self.R,self.M,self.K=[x@x.T for x in B[:3]];self.B=np.asarray(B[3:])
        self.den=1+h*self.gamma+h*h*self.om2/4
        self.S=self.B*(h/(2*self.den[:,None,:]))
        H=self.R+2*self.M/h+h*self.K/2+np.einsum('jik,jlk->il',self.S,self.B)
        self.diag=2*m/h+d+h*k/2
        self.solver=solver
        if solver=='dense':
            self.fac=cho_factor(np.diag(self.diag)+A.T@H@A)
        else:
            # H=L L^T, Woodbury without inversion of a possibly singular H.
            self.U=A.T@factor_psd(H);self.V=self.U/self.diag[:,None]
            self.fac=cho_factor(np.eye(H.shape[0])+self.U.T@self.V)
        self.q=np.zeros(n);self.v=self.q.copy()
        self.x=np.zeros((len(centers),A.shape[0]));self.a=self.x.copy()
    def energy(self):
        u=self.A@self.v;z=self.A@self.q
        return .5*float(np.sum(self.m*self.v**2+self.k*self.q**2)+u@self.M@u+z@self.K@z+np.sum(self.a**2+self.om2*self.x**2))
    def step(self,F):
        F=np.asarray(F)
        if F.shape!=self.v.shape or np.iscomplexobj(F) or not np.isfinite(F).all():raise ValueError('invalid force')
        h=self.h;u=self.A@self.v;z=self.A@self.q
        free=(self.a-h*self.om2*self.x/2)/self.den
        rhs=2*self.m*self.v/h-self.k*self.q+F+self.A.T@(2*self.M@u/h-self.K@z-np.einsum('jik,jk->i',self.B,free))
        if self.solver=='dense':vm=cho_solve(self.fac,rhs)
        else:
            y=rhs/self.diag;vm=y-self.V@cho_solve(self.fac,self.U.T@y)
        mid=self.A@vm;am=free+np.einsum('jik,i->jk',self.S,mid)
        self.q+=h*vm;self.v=2*vm-self.v;self.x+=h*am;self.a=2*am-self.a
        ds=h*float(np.sum(self.d*vm**2));da=h*float(mid@self.R@mid+2*self.gamma*np.sum(am**2))
        return h*float(vm@F),ds,da

def synthetic(n,rate,solver):
    rng=np.random.default_rng(731)
    m=np.linspace(.7,1.3,n);f=np.geomspace(35,2400,n);k=m*(2*np.pi*f)**2;d=2*m*3.
    A=rng.normal(size=(4,n))/np.sqrt(n)
    centers=np.array([70.,120.,250.,400.,800.])
    C=np.stack([np.eye(4)*.5,np.eye(4)*.004,np.eye(4)*100.,*[rng.normal(size=(4,4)) for _ in centers]])
    C[3:]=C[3:]@C[3:].transpose(0,2,1)*20
    return CoupledModal(m,k,d,A,C,centers,7.,rate,solver)

def probe(n,rate,seconds=.12):
    a=synthetic(n,rate,'lowrank');b=synthetic(n,rate,'dense')
    W=L=absolute=peak=err=state=0.;minimum=0.
    direction=np.cos(np.arange(n));direction/=np.linalg.norm(direction)
    for i in range(round(rate*seconds)):
        t=(i+.5)/rate
        F=direction*np.sin(2*np.pi*130*t)*np.sin(np.pi*t/.025)**2 if t<.025 else np.zeros(n)
        w,ds,da=a.step(F);b.step(F);W+=w;L+=ds+da;absolute+=abs(w)
        E=a.energy();peak=max(peak,E);err=max(err,abs(W-L-E));minimum=min(minimum,ds,da)
        state=max(state,relative(a.v,b.v),relative(a.q,b.q),relative(a.a,b.a),relative(a.x,b.x))
        if not np.isfinite([W,L,E,state]).all():raise ValueError('nonfinite coupled state')
    budget=err/max(absolute,peak,1e-30)
    return dict(structuralModes=n,sampleRate=rate,samples=round(rate*seconds),energyRelative=budget,denseStateRelative=state,
        minimumLoss=minimum,gate=bool(budget<=1e-9 and state<=1e-8 and minimum>=-1e-14))

def timing(n,rate=48000,blocks=9,samples=256):
    rows=[];F=np.ones(n)/np.sqrt(n)
    for solver in ('dense','lowrank'):
        a=synthetic(n,rate,solver)
        for _ in range(256):a.step(F)
        elapsed=[]
        for _ in range(blocks):
            t=time.perf_counter_ns()
            for _ in range(samples):a.step(F)
            elapsed.append((time.perf_counter_ns()-t)/samples/1000)
        rows.append(dict(solver=solver,medianUs=float(np.median(elapsed)),p95Us=float(np.percentile(elapsed,95)),samplesPerBlock=samples,blocks=blocks))
    return dict(structuralModes=n,timings=rows,speedup=rows[0]['medianUs']/rows[1]['medianUs'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[probe(n,r) for n in (32,64,128) for r in (44100,48000,96000)]
    times=[timing(n) for n in (32,64,128,256)]
    gate=all(x['gate'] for x in rows)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,physicalFitAccepted=False,boardFields=4,
        structuralModeCounts=[32,64,128],maximumEnergyError=max(x['energyRelative'] for x in rows),
        maximumDenseStateError=max(x['denseStateRelative'] for x in rows),timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'coupled_modal_midpoint.json').write_text(json.dumps(dict(summary=summary,cases=rows,benchmark=times),indent=2,allow_nan=False))
    print('G3_COUPLED_MIDPOINT_GATE '+json.dumps(summary),flush=True)
    print('G3_COUPLED_MIDPOINT_BENCHMARK '+json.dumps(times),flush=True)
    if not gate:raise ValueError('coupled midpoint diagnostic failed')
if __name__=='__main__':main()

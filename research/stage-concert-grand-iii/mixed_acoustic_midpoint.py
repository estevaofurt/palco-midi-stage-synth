"""G3.12w: mixed passive acoustic realization coupled to dry mechanics.
Synthetic coefficients and port maps only. Independent energy-coordinate
first-order midpoint reference. No fitted radiation or pressure observer."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky,cho_factor,cho_solve,solve,solve_triangular
from passive_radiation import factor_psd
from baffle_passive_fit import evaluate,audit
from wire_physical_midpoint import CoupledWire,load
from split_radiation import relative

class Mixed:
    def __init__(self,M,K,D,P,A,C,cfg,rate):
        self.K=K;self.D=D;self.P=P;self.A=A;self.h=1/rate
        self.a=2*np.pi*np.asarray(cfg['relax']);self.w=2*np.pi*np.asarray(cfg['osc']);self.g=2*np.pi*cfg['gamma']
        if len(C)!=1+len(self.a)+len(self.w) or not audit(C,cfg)['gate']:raise ValueError('invalid passive load')
        self.R=np.stack([factor_psd(x) for x in C[1:1+len(self.a)]])
        self.B=np.stack([factor_psd(x) for x in C[1+len(self.a):]])
        self.M=M+A.T@C[0]@A
        h=self.h;self.dr=1+h*self.a/2;self.do=1+h*self.g+h*h*self.w*self.w/4
        Z=np.einsum('j,jik,jlk->il',1/self.dr,self.R,self.R)+np.einsum('j,jik,jlk->il',h/(2*self.do),self.B,self.B)
        H=2*self.M/h+D+h*K/2+A.T@Z@A
        self.scale=1/np.sqrt(np.diag(self.M));self.fac=cho_factor(H*(self.scale[:,None]*self.scale[None,:]))
        self.q=np.zeros(len(M));self.v=self.q.copy()
        self.x=np.zeros((len(self.a),len(A)));self.y=np.zeros((len(self.w),len(A)));self.u=self.y.copy()
    def energy(self):
        return .5*float(self.q@self.K@self.q+self.v@self.M@self.v+np.sum(self.a[:,None]*self.x**2)+np.sum(self.w[:,None]**2*self.y**2+self.u**2))
    def step(self,F):
        h=self.h
        r=-self.a[:,None]*self.x/self.dr[:,None]
        o=(self.u-h*self.w[:,None]**2*self.y/2)/self.do[:,None]
        free=np.einsum('jik,jk->i',self.R,r)+np.einsum('jik,jk->i',self.B,o)
        mid=self.scale*cho_solve(self.fac,self.scale*(2*self.M@self.v/h-self.K@self.q+self.P@F-self.A.T@free))
        z=self.A@mid
        dx=r+np.einsum('jik,i->jk',self.R,z)/self.dr[:,None]
        vm=o+h/2*np.einsum('jik,i->jk',self.B,z)/self.do[:,None]
        losses=h*np.array([mid@self.D@mid,np.sum(dx*dx),2*self.g*np.sum(vm*vm)])
        obs=self.P.T@mid;work=h*float(F@obs)
        self.q+=h*mid;self.v=2*mid-self.v
        self.x+=h*dx;self.y+=h*vm;self.u=2*vm-self.u
        return obs,work,losses

class Reference:
    """Assemble the first-order ODE in Euclidean energy coordinates.
    Relaxation uses xdot=R^T A v-a x; reaction R xdot.
    Inertance is included in mass once. Oscillators are reciprocal."""
    def __init__(self,m):
        n=len(m.q);p=len(m.A);nr=len(m.a)*p;no=len(m.w)*p
        self.h=m.h;self.Lk=cholesky(m.K,lower=True);self.Lm=cholesky(m.M,lower=True)
        inv=solve_triangular(self.Lm.T,np.eye(n),lower=False);S=m.A@inv
        self.S=S;self.inv=inv;self.D=m.D;self.g=m.g
        a=np.repeat(np.sqrt(m.a),p);w=np.repeat(m.w,p)
        R=np.concatenate([x for x in m.R],axis=1);B=np.concatenate([x for x in m.B],axis=1)
        self.R=R;self.a=a
        self.sl=(slice(0,n),slice(n,2*n),slice(2*n,2*n+nr),slice(2*n+nr,2*n+nr+no),slice(2*n+nr+no,2*n+nr+2*no))
        q,v,x,y,u=self.sl;N=u.stop;L=np.zeros((N,N));J=self.Lk.T@inv
        L[q,v]=J;L[v,q]=-J.T
        L[v,v]=-inv.T@m.D@inv-S.T@R@R.T@S
        L[v,x]=(S.T@R)*a;L[x,v]=a[:,None]*(R.T@S);L[x,x]=-np.diag(a*a)
        L[v,u]=-S.T@B;L[u,v]=B.T@S
        L[y,u]=np.diag(w);L[u,y]=-np.diag(w);L[u,u]=-2*m.g*np.eye(no)
        if np.linalg.eigvalsh((L+L.T)/2).max()>1e-7*max(np.linalg.norm(L),1.):raise ValueError('reference not passive')
        self.G=np.zeros((N,m.P.shape[1]));self.G[v]=inv.T@m.P
        self.T=solve(np.eye(N)-m.h*L/2,np.eye(N));self.z=np.zeros(N)
    def pack(self,m):
        return np.r_[self.Lk.T@m.q,self.Lm.T@m.v,(np.sqrt(m.a)[:,None]*m.x).ravel(),(m.w[:,None]*m.y).ravel(),m.u.ravel()]
    def step(self,F):
        h=self.h;mid=self.T@(self.z+h/2*self.G@F);self.z=2*mid-self.z
        q,v,x,y,u=self.sl;vel=self.inv@mid[v]
        dx=self.R.T@(self.S@mid[v])-self.a*mid[x]
        losses=h*np.array([vel@self.D@vel,dx@dx,2*self.g*(mid[u]@mid[u])])
        obs=self.G.T@mid
        return obs,h*float(F@obs),losses

def fixture_weights(p):
    C=[]
    for j,scale in enumerate((.03,.2,.15,500.,800.)):
        b=np.eye(p)+.15*np.cos(np.arange(p*p).reshape(p,p)+j)
        C.append(scale*b@b.T)
    return np.stack(C),dict(relax=[40.,150.],osc=[80.,240.],gamma=35.,ridge=0.)

def proof(M,K,D,P,A,rate,steps=1024):
    C,cfg=fixture_weights(len(A));m=Mixed(M,K,D,P,A,C,cfg,rate);r=Reference(m)
    work=0.;loss=np.zeros(3);peak=state=ledger=balance=observer=0.
    for t in range(steps):
        F=np.sin(.067*t+np.arange(P.shape[1]))*(t<steps//3)
        o,w,l=m.step(F);p,v,d=r.step(F);work+=w;loss+=l
        E=m.energy();peak=max(peak,E,abs(work),loss.sum(),1e-30)
        state=max(state,float(np.linalg.norm(r.pack(m)-r.z)/np.sqrt(2*peak)))
        observer=max(observer,relative(o,p))
        ledger=max(ledger,abs(w-v)/peak,float(np.linalg.norm(l-d)/peak))
        balance=max(balance,abs(E+loss.sum()-work)/peak,abs(.5*(r.z@r.z)+loss.sum()-work)/peak)
        if min(l.min(),d.min())<-1e-14:raise ValueError('negative loss')
    return dict(gate=bool(max(state,ledger,balance,observer)<=1e-7 and min(loss)>0),
        rate=rate,coordinates=len(M),fields=len(A),steps=steps,stateEnergyRelative=state,ledgerRelative=ledger,
        energyRelative=balance,observerRelative=observer,mechanicalLossJ=float(loss[0]),relaxationLossJ=float(loss[1]),oscillatorLossJ=float(loss[2]),
        positiveReal=audit(C,cfg))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale);cases=[]
    for rate in (48000,96000):
        for n in (16,32):
            model=CoupledWire(z['stiffness'],z['damping'],z['ports'],z['wirePorts'],wires,rate,n)
            M,K,D,P=model.matrices()
            # Diagnostic map only: three normalized structural force-port directions.
            B=z['ports'][:,4:7].T;B=B/np.linalg.norm(B,axis=1)[:,None]
            A=np.column_stack([B,np.zeros((len(B),len(M)-80))])
            row=dict(partials=n,**proof(M,K,D,P,A,rate));cases.append(row)
            print('G3_MIXED_ACOUSTIC_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=all(v['gate'] for v in cases),cases=len(cases),syntheticCoefficients=True,syntheticPortMap=True,
        physicalAcousticFitAccepted=False,causalPressureObserverIncluded=False,diagnosticOnly=True,
        maximumEnergyError=max(v['energyRelative'] for v in cases),maximumStateError=max(v['stateEnergyRelative'] for v in cases),
        timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'mixed_acoustic_midpoint.json').write_text(json.dumps(dict(summary=summary,cases=cases,sourceFrozenSha256=sha),indent=2,allow_nan=False))
    print('G3_MIXED_ACOUSTIC_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('mixed acoustic midpoint proof failed')
if __name__=='__main__':main()

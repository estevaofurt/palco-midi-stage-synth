"""G3.14d.9: acoustic memory port on physical wire midpoint.
Only synthetic passive FIR loads in this experiment. Dry solver unchanged."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from wire_physical_midpoint import CoupledWire,load
from acoustic_cq_pilot import convolve
from split_radiation import relative

class WireAcoustic(CoupledWire):
    def __init__(self,k,D,P,A,wires,rate,partials,U,W):
        super().__init__(k,D,P,A,wires,rate,partials)
        self.U=np.array(U,float,copy=True);self.W=np.array(W,float,copy=True)
        m=self.U.shape[1];h=self.h
        if self.U.shape[0]!=self.n or self.W.ndim!=3 or self.W.shape[1:]!=(m,m) or len(self.W)<1:raise ValueError('acoustic shape')
        if not np.isfinite(self.W).all() or relative(self.U.T@self.U,np.eye(m))>1e-10 or relative(self.W,self.W.transpose(0,2,1))>1e-10:raise ValueError('acoustic coordinates')
        H=2/h*self.Mb+self.Db+h*self.Kb/2-self.A.T@(np.sum(self.C*self.C/self.Hi,axis=1)[:,None]*self.A)
        self.fac=cho_factor((H+H.T)/2+self.U@self.W[0]@self.U.T)
        self.history=np.zeros((len(W)-1,m))
    def step(self,F):
        h=self.h
        b,i=self.apply(self.v,self.u,self.Mb,self.mi,1.)
        g,j=self.apply(self.q,self.x,self.Kb,self.ki,self.ks)
        memory=np.einsum('kij,kj->i',self.W[1:],self.history)
        rb=2*b/h-g+self.P@F-self.U@memory;ri=2*i/h-j+self.F@F
        vm=cho_solve(self.fac,rb-self.A.T@np.sum(self.C*ri/self.Hi,axis=1))
        um=(ri-self.C*(self.A@vm)[:,None])/self.Hi
        y=self.U.T@vm;force=self.W[0]@y+memory
        db,di=self.apply(vm,um,self.Db,self.di,self.ds)
        obs=self.P.T@vm+np.einsum('wip,wi->p',self.F,um)
        loss=h*float(vm@db+np.sum(um*di));work=h*float(F@obs);air=h*float(y@force)
        self.q+=h*vm;self.x+=h*um;self.v=2*vm-self.v;self.u=2*um-self.u
        if len(self.history):
            self.history[1:]=self.history[:-1].copy();self.history[0]=y
        return obs,work,loss,air,y,force

def fixture_load(n):
    U=np.eye(n)[:,:min(4,n)];R=np.diag(np.linspace(.1,.4,U.shape[1]))
    # PSD FIR R(1-z): acoustic port work is nonnegative for every
    # finite zero-prehistory trajectory; not a physical radiation model.
    return U,np.stack([R,-R])

def compare(k,D,P,A,wires,rate,partials,steps=512,wet=True):
    U,W=fixture_load(len(k))
    if not wet:W=np.zeros((1,U.shape[1],U.shape[1]))
    a=WireAcoustic(k,D,P,A,wires,rate,partials,U,W)
    dry=CoupledWire(k,D,P,A,wires,rate,partials)
    M,K,drag,B=dry.matrices();h=a.h
    T=np.zeros((len(M),U.shape[1]));T[:len(k)]=U
    H=2*M/h+drag+h*K/2+T@W[0]@T.T
    # Scale the independent dense solve for the stiff wire coordinates.
    scale=1/np.sqrt(np.diag(M));fac=cho_factor(H*(scale[:,None]*scale[None,:]))
    q=np.zeros(len(M));v=q.copy();history=np.zeros((len(W)-1,U.shape[1]))
    F=np.random.default_rng(194).normal(size=(steps,P.shape[1]));F[steps//2:]=0.
    Y=[];G=[];O=[];Oref=[];work=loss=air=peak=balance=0.;minimum=0.;dryError=0.
    denseWork=denseLoss=denseAir=denseBalance=0.
    for f in F:
        obs,ww,ll,aa,y,g=a.step(f);Y.append(y);G.append(g);O.append(obs)
        mem=np.einsum('kij,kj->i',W[1:],history)
        vm=scale*cho_solve(fac,scale*(2*M@v/h-K@q+B@f-T@mem))
        yr=T.T@vm;fr=W[0]@yr+mem;Oref.append(B.T@vm)
        q+=h*vm;v=2*vm-v
        if len(history):
            history[1:]=history[:-1].copy();history[0]=yr
        denseWork+=h*float(f@(B.T@vm));denseLoss+=h*float(vm@drag@vm);denseAir+=h*float(yr@fr)
        E=a.energy();work+=ww;loss+=ll;air+=aa;minimum=min(minimum,air)
        peak=max(peak,E,abs(work),loss,abs(air),1e-30)
        balance=max(balance,abs(E+loss+air-work)/peak)
        Er=.5*float(v@M@v+q@K@q);denseBalance=max(denseBalance,abs(Er+denseLoss+denseAir-denseWork)/peak)
        if not wet:
            o,_,_=dry.step(f);dryError=max(dryError,relative(obs,o))
    state=max(relative(np.r_[a.q,a.x.ravel()],q),relative(np.r_[a.v,a.u.ravel()],v))
    obs=relative(np.asarray(O),np.asarray(Oref))
    replay=relative(np.asarray(G),convolve(W,np.asarray(Y))) if wet else 0.
    mw=minimum/max(peak,1e-30)
    row=dict(rate=rate,partials=partials,steps=steps,wet=wet,finalStateRelative=state,
        observerRelative=obs,energyRelative=balance,denseEnergyRelative=denseBalance,
        convolutionReplayRelative=replay,dryReplayRelative=dryError,minimumAcousticWorkRelative=mw,acousticWorkJ=air)
    row['gate']=bool(max(state,obs,balance,denseBalance,replay,dryError)<=1e-8 and mw>=-1e-8)
    return row

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    rows=[]
    for rate in (48000,96000):
        for n in (8,16):
            for wet in (False,True):
                row=compare(z['stiffness'],z['damping'],z['ports'],z['wirePorts'],wires,rate,n,wet=wet)
                rows.append(row);print('G3_WIRE_ACOUSTIC_PORT_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=all(r['gate'] for r in rows),diagnosticOnly=True,cases=len(rows),sourceFrozenSha256=sha,
        physicalWireCoordinates=True,syntheticPassiveLoad=True,physicalRadiationIntegrated=False,
        hammerIncluded=False,damperControlIncluded=False,audibleSustainMeasured=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'wire_acoustic_port.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_WIRE_ACOUSTIC_PORT_GATE '+json.dumps(summary,allow_nan=False),flush=True)
    if not summary['gate']:raise ValueError('wire acoustic port mismatch')
if __name__=='__main__':main()

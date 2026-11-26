"""G3.11l: synthetic string partials coupled reciprocally to four board fields.
Schur elimination of independent string DOFs; a dense augmented midpoint
is an independent reference. No rejected acoustic fit or real piano calibration."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from contiguous_midpoint import stress_model
from passive_midpoint import factor_psd
from split_radiation import relative

class StringBoard:
    def __init__(self,board,ms,ks,ds,G,kc,dc,solver='schur'):
        self.b=board;self.h=h=board.h
        self.ms,self.ks,self.ds,self.G,self.kc,self.dc=[np.asarray(v,dtype=float).copy() for v in (ms,ks,ds,G,kc,dc)]
        n=len(board.m);s=len(self.ms);p=board.A.shape[0]
        if any(v.shape!=(s,) for v in (self.ms,self.ks,self.ds,self.kc,self.dc)) or self.G.shape!=(s,p) or not s or not all(np.isfinite(v).all() for v in (self.ms,self.ks,self.ds,self.G,self.kc,self.dc)) or np.any(self.ms<=0) or any(np.any(v<0) for v in (self.ks,self.ds,self.kc,self.dc)) or solver not in ('schur','dense'):raise ValueError('invalid string parameters')
        self.q=np.zeros(s);self.v=np.zeros(s);self.solver=solver
        self.c=self.dc+h*self.kc/2
        self.base=2*self.ms/h+self.ds+h*self.ks/2
        self.hs=self.base+self.c
        H=board.R+2*board.M/h+h*board.K/2+np.einsum('jik,jlk->il',board.S,board.B)
        self.Aug=np.column_stack((board.A,np.zeros((p,s))))
        if solver=='schur':
            eff=self.c*self.base/self.hs
            H=H+self.G.T@(eff[:,None]*self.G)
            self.U=board.A.T@factor_psd(H);self.V=self.U/board.diag[:,None]
            self.fac=cho_factor(np.eye(p)+self.U.T@self.V)
        else:
            # Assemble the complete coupled structure independently.
            J=np.column_stack((-self.G@board.A,np.eye(s)))
            self.M0=np.diag(np.r_[board.m,self.ms])
            self.K0=np.diag(np.r_[board.k,self.ks])+J.T@(self.kc[:,None]*J)
            self.D0=np.diag(np.r_[board.d,self.ds])+J.T@(self.dc[:,None]*J)
            self.fac=cho_factor(2*self.M0/h+self.D0+h*self.K0/2+self.Aug.T@H@self.Aug)

    def energy(self):
        b=self.b;rel=self.q-self.G@(b.A@b.q)
        return b.energy()+.5*float(np.sum(self.ms*self.v**2+self.ks*self.q**2+self.kc*rel**2))

    def step(self,Fb,Fs):
        b=self.b;h=self.h;Fb=np.asarray(Fb);Fs=np.asarray(Fs)
        if Fb.shape!=b.v.shape or Fs.shape!=self.v.shape or np.iscomplexobj(Fb) or np.iscomplexobj(Fs) or not np.isfinite(Fb).all() or not np.isfinite(Fs).all():raise ValueError('invalid external force')
        u=b.A@b.v;z=b.A@b.q;rel=self.q-self.G@z
        free=(b.a-h*b.om2*b.x/2)/b.den
        air=2*b.M@u/h-b.K@z-np.einsum('jik,jk->i',b.B,free)
        if self.solver=='schur':
            rhs_s=2*self.ms*self.v/h-self.ks*self.q+Fs-self.kc*rel
            g=self.G.T@(self.kc*rel+self.c*rhs_s/self.hs)
            rhs=2*b.m*b.v/h-b.k*b.q+Fb+b.A.T@(air+g)
            y=rhs/b.diag;vm=y-self.V@cho_solve(self.fac,self.U.T@y)
            mid=b.A@vm;sm=(rhs_s+self.c*(self.G@mid))/self.hs
        else:
            rhs=2*self.M0@np.r_[b.v,self.v]/h-self.K0@np.r_[b.q,self.q]+np.r_[Fb,Fs]+self.Aug.T@air
            vv=cho_solve(self.fac,rhs);vm=vv[:len(b.m)];sm=vv[len(b.m):];mid=b.A@vm
        am=free+np.einsum('jik,i->jk',b.S,mid)
        rv=sm-self.G@mid
        work=h*float(vm@Fb+sm@Fs)
        ds=h*float(np.sum(b.d*vm**2)+np.sum(self.ds*sm**2))
        dc=h*float(np.sum(self.dc*rv**2))
        da=h*float(mid@b.R@mid+2*b.gamma*np.sum(am**2))
        b.q+=h*vm;b.v=2*vm-b.v;b.x+=h*am;b.a=2*am-b.a
        self.q+=h*sm;self.v=2*sm-self.v
        return np.array([work,ds,dc,da])

def fixture(voices,partials,rate,solver,board_modes=64):
    b=stress_model(board_modes,5,rate)
    # Synthetic partials, not measured string or bridge parameters.
    f=110*2**(np.arange(voices)/24);f=(f[:,None]*np.arange(1,partials+1)).ravel()
    n=len(f);rng=np.random.default_rng(932)
    m=np.linspace(.02,.04,n);k=m*(2*np.pi*f)**2;d=.5*m
    G=np.repeat(rng.normal(size=(voices,4)),partials,axis=0)/np.sqrt(4*partials)
    kc=.025*k;dc=.02*np.sqrt(m*kc)
    return StringBoard(b,m,k,d,G,kc,dc,solver)

def probe(voices,partials,rate,seconds=.06,board_modes=64):
    a=fixture(voices,partials,rate,'schur',board_modes)
    b=fixture(voices,partials,rate,'dense',board_modes)
    W=L=absolute=peak=err=state=ledger=0.;minimum=0.
    Fb=np.zeros(board_modes);direction=np.cos(np.arange(voices*partials));direction/=np.linalg.norm(direction)
    for i in range(round(seconds*rate)):
        t=(i+.5)/rate
        Fs=direction*np.sin(2*np.pi*130*t)*np.sin(np.pi*t/.015)**2 if t<.015 else np.zeros_like(direction)
        w=a.step(Fb,Fs);v=b.step(Fb,Fs)
        W+=w[0];L+=w[1:].sum();absolute+=abs(w[0]);minimum=min(minimum,float(w[1:].min()))
        E=a.energy();peak=max(peak,E);err=max(err,abs(W-L-E));ledger=max(ledger,relative(w,v))
        state=max(state,*(relative(getattr(a,k),getattr(b,k)) for k in ('q','v')),
            *(relative(getattr(a.b,k),getattr(b.b,k)) for k in ('q','v','x','a')))
        if not np.isfinite([W,L,E,state,ledger]).all():raise ValueError('nonfinite coupled state')
    budget=err/max(absolute,peak,1e-30)
    return dict(syntheticVoices=voices,partialsPerVoice=partials,stringDOFs=voices*partials,boardModes=board_modes,sampleRate=rate,
        energyRelative=budget,stateRelative=state,ledgerRelative=ledger,minimumLoss=minimum,gate=bool(budget<=1e-9 and max(state,ledger)<=1e-8 and minimum>=-1e-14))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[probe(v,j,r) for v in (32,64) for j in (1,4) for r in (44100,48000,96000)]
    gate=all(v['gate'] for v in rows)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,boardFields=4,maximumSyntheticVoices=64,maximumStringDOFs=256,
        maximumEnergyError=max(v['energyRelative'] for v in rows),maximumStateError=max(v['stateRelative'] for v in rows),
        maximumLedgerError=max(v['ledgerRelative'] for v in rows),physicalFitAccepted=False,timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'string_board_schur.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_STRING_BOARD_GATE '+json.dumps(summary),flush=True)
    if not gate:raise ValueError('string coupling diagnostic failed')
if __name__=='__main__':main()

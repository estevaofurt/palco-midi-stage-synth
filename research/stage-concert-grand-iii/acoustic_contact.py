"""G3.14d.10: hammer/pedal compatibility with a synthetic acoustic port.
Signed acoustic work is separate from irreversible losses.
No physical radiation feedback, pressure, or approved sound."""
import argparse,copy,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor
from wire_physical_midpoint import CoupledWire,load
from wire_acoustic_port import WireAcoustic,fixture_load
from physical_pedal_repeat import PointSchur,PointDense,Repeating,damper_ports
from variable_damper import PedalControl
from felt_law import params

class Memory:
    def init_memory(self,U,W):
        self.projection=U;self.weights=W;self.history=np.zeros((len(W)-1,U.shape[1]))
        self.air=0.;self.minimumAir=0.
    def memory(self):
        return np.einsum('kij,kj->i',self.weights[1:],self.history)
    def advance(self,v,mem):
        y=self.projection.T@v;f=self.weights[0]@y+mem
        self.air+=self.h*float(y@f);self.minimumAir=min(self.minimumAir,self.air)
        if len(self.history):
            self.history[1:]=self.history[:-1].copy();self.history[0]=y

class AcousticSchur(PointSchur,Memory):
    def __init__(self,a,B,I):
        super().__init__(a,B,I);self.init_memory(a.U,a.W)
    def free(self):
        a=self.a;b,i=a.apply(a.v,a.u,a.Mb,a.mi,1.)
        g,j=a.apply(a.q,a.x,a.Kb,a.ki,a.ks)
        v,u=self.solve((2*b/self.h-g-self.projection@self.memory())[:,None],(2*i/self.h-j)[:,:,None])
        return self.observe(v[:,0],u[:,:,0])
    def step(self,F):
        a=self.a;h=self.h;mem=self.memory()
        b,i=a.apply(a.v,a.u,a.Mb,a.mi,1.);g,j=a.apply(a.q,a.x,a.Kb,a.ki,a.ks)
        vv,uu=self.solve((2*b/h-g+a.P@F-self.projection@mem)[:,None],(2*i/h-j+a.F@F)[:,:,None])
        v=vv[:,0];u=uu[:,:,0];db,di=a.apply(v,u,a.Db,a.di,a.ds)
        intrinsic=h*float(v@db+np.sum(u*di))
        damper=self.B.T@v+np.einsum('wip,wi->p',self.I,u)
        extra=h*float(self.d@(damper*damper));self.loss+=extra
        obs=self.observe(v,u);work=h*float(F@obs)
        a.q+=h*v;a.x+=h*u;a.v=2*v-a.v;a.u=2*u-a.u
        self.advance(v,mem)
        return obs,work,intrinsic+extra

class AcousticDense(PointDense,Memory):
    def __init__(self,a,B,I,U,W):
        T=np.zeros((a.n+a.nw*a.partials,U.shape[1]));T[:a.n]=U
        self.init_memory(T,W);super().__init__(a,B,I)
    def set_levels(self,d):
        super().set_levels(d)
        H=2*self.M/self.h+self.D+self.h*self.K/2+self.projection@self.weights[0]@self.projection.T
        self.fac=cho_factor(H*(self.s[:,None]*self.s[None,:]))
    def free(self):
        return self.P.T@self.solve(2*self.M@self.v/self.h-self.K@self.q-self.projection@self.memory())
    def step(self,F):
        h=self.h;mem=self.memory()
        v=self.solve(2*self.M@self.v/h-self.K@self.q+self.P@F-self.projection@mem)
        self.q+=h*v;self.v=2*v-self.v;obs=self.P.T@v
        damper=self.Q.T@v;self.loss+=h*float(self.d@(damper*damper))
        self.advance(v,mem)
        return obs,h*float(F@obs),h*float(v@self.D@v)

def probe(z,wires,rows,groups,masses,felts,rate,n,pedal,wet):
    ww=copy.deepcopy(wires)
    for j,w in enumerate(ww):w.port=j
    k,D,A=z['stiffness'],z['damping'],z['wirePorts'];P=np.zeros((len(k),len(ww)))
    U,W=fixture_load(len(k))
    if not wet:W=np.zeros((1,U.shape[1],U.shape[1]))
    a=WireAcoustic(k,D,P,A,ww,rate,n,U,W);b=CoupledWire(k,D,P,A,ww,rate,n)
    B,I=damper_ports(a,rows)
    x=Repeating(AcousticSchur(a,B,I),groups,masses,felts)
    y=Repeating(AcousticDense(b,B,I,U,W),groups,masses,felts,True)
    ctrl=PedalControl(len(masses),rate,transition_ms=5.);ctrl.sustain(pedal)
    group=np.asarray(groups);strength=2./np.bincount(group)[group]
    state=balance=force=peak=contact=work=0.;mismatch=0
    for t in range(round(.085*rate)):
        if t in (0,round(.030*rate)):
            for j,s in enumerate((.5,1.,1.5,2.)):
                ctrl.note(j,True)
                if not x.launch(j,s) or not y.launch(j,s):raise ValueError('launch rejected')
        if t in (round(.010*rate),round(.040*rate)):
            for j in range(len(masses)):ctrl.note(j,False)
        if t==round(.065*rate):ctrl.sustain(0.)
        d=strength*ctrl.advance()[group];x.damp(d);y.damp(d)
        F,c,w,_=x.step();R,d,v,_=y.step()
        peak=max(peak,float(F.max()));force=max(force,float(np.max(abs(F-R))))
        contact=max(contact,c,d);work=max(work,w,v);mismatch+=int(not np.array_equal(x.active,y.active))
        q,u=x.a.state();qr,ur=y.a.state();dq=q-qr;dv=u-ur
        E=.5*float(dq@y.a.K@dq+dv@y.a.M@dv)
        state=max(state,np.sqrt(max(0.,E)/max(x.injected,1e-30)))
        for bank in (x,y):
            balance=max(balance,abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss+bank.a.air-bank.injected)/max(bank.injected,1e-30))
    airError=abs(x.a.air-y.a.air)/x.injected
    row=dict(rate=rate,partials=n,pedal=pedal,wet=wet,launches=x.launches,captures=x.captures,
        captureMismatchSteps=mismatch,energyRelative=balance,stateEnergyRelative=state,
        forceRelative=force/max(peak,1e-30),contactResidualM=contact,workResidualJ=work,
        acousticWorkJ=x.a.air,denseAcousticWorkJ=y.a.air,acousticWorkRelative=airError,
        minimumAcousticWorkRelative=min(x.a.minimumAir,y.a.minimumAir)/x.injected,damperLossJ=x.a.loss)
    row['gate']=bool(x.launches==x.captures==2*len(masses) and y.captures==x.captures and mismatch==0 and x.a.loss>0
        and max(balance,state,row['forceRelative'],airError)<=1e-8 and contact<=1e-12 and work<=1e-10
        and row['minimumAcousticWorkRelative']>=-1e-8 and (x.a.air>0 if wet else x.a.air==0.))
    return row

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    rows={r['key']:r for r in json.loads(a.scale.read_text())['rows']};root=Path(__file__).parent
    pars=[params(k,rows[k]['count'],json.loads((root/'physical_sources.json').read_text()),json.loads((root/'felt_hypothesis.json').read_text())) for k in (45,48,60,64)]
    groups=[w.port for w in wires];masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    cases=[]
    for rate in (48000,96000):
        for pedal in (0.,1.):
            for wet in (False,True):
                v=probe(z,wires,rows,groups,masses,felts,rate,16,pedal,wet);cases.append(v)
                print('G3_ACOUSTIC_CONTACT_CASE '+json.dumps(v,allow_nan=False),flush=True)
    summary=dict(gate=all(v['gate'] for v in cases),diagnosticOnly=True,cases=len(cases),syntheticPassiveLoad=True,
        physicalRadiationIntegrated=False,audibleSustainMeasured=False,sourceFrozenSha256=sha)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'acoustic_contact.json').write_text(json.dumps(dict(summary=summary,cases=cases),indent=2,allow_nan=False))
    print('G3_ACOUSTIC_CONTACT_GATE '+json.dumps(summary,allow_nan=False),flush=True)
    if not summary['gate']:raise ValueError('acoustic contact mismatch')
if __name__=='__main__':main()

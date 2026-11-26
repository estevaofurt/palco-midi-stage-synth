"""G3.12i: dry midpoint dynamics for physically attached wires.
Exact Schur elimination of normalized wire interiors; retain all rear
mass, stiffness and damping cross terms. No acoustic fit or hammer law."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from string_structure import Wire
from acoustic_matrix_archive import read_npz
from wire_port_enrichment import development_grids,comparison
from modal_string_radiation import response as harmonic_reference
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

class CoupledWire:
    def __init__(self,k,D,P,A,wires,rate,partials):
        self.k=np.asarray(k);self.D=np.asarray(D);self.P=np.asarray(P).copy()
        self.A=np.asarray(A);self.wires=wires;self.h=1/rate;self.n=len(k);self.nw=len(wires);self.partials=partials
        n=self.n;h=self.h
        if self.A.shape!=(len(wires),n) or D.shape!=(n,n) or P.shape[0]!=n or partials<1 or any(partials>len(w.w2) for w in wires):raise ValueError('wire dimensions')
        self.mi=np.stack([w.m[:partials] for w in wires]);self.ki=np.stack([w.k[:partials] for w in wires]);self.di=np.stack([w.d[:partials] for w in wires])
        self.ks=np.stack([w.w2[:partials] for w in wires]);self.ds=np.stack([w.gamma[:partials] for w in wires])
        self.m0=np.array([w.M[0,0] for w in wires]);self.k0=np.array([w.K[0,0] for w in wires]);self.d0=np.array([w.D[0,0] for w in wires])
        self.F=np.zeros((len(wires),partials,P.shape[1]))
        for j,w in enumerate(wires):
            self.P[:,w.port]+=w.P[0]*self.A[j];self.F[j,:,w.port]=w.p[:partials]
        self.Mb=np.eye(n)+self.A.T@(self.m0[:,None]*self.A)
        self.Kb=np.diag(k)+self.A.T@(self.k0[:,None]*self.A)
        self.Db=D+self.A.T@(self.d0[:,None]*self.A)
        self.Hi=2/h+self.ds+h*self.ks/2
        self.C=2/h*self.mi+self.di+h*self.ki/2
        H=2/h*self.Mb+self.Db+h*self.Kb/2-self.A.T@(np.sum(self.C*self.C/self.Hi,axis=1)[:,None]*self.A)
        self.fac=cho_factor((H+H.T)/2)
        self.q=np.zeros(n);self.v=np.zeros(n);self.x=np.zeros_like(self.ks);self.u=np.zeros_like(self.ks)
    def apply(self,b,i,b0,c,diag):
        rear=self.A@b
        return b0@b+self.A.T@np.sum(c*i,axis=1),diag*i+c*rear[:,None]
    def energy(self):
        Mv,Mu=self.apply(self.v,self.u,self.Mb,self.mi,1.)
        Kq,Kx=self.apply(self.q,self.x,self.Kb,self.ki,self.ks)
        return .5*float(self.v@Mv+np.sum(self.u*Mu)+self.q@Kq+np.sum(self.x*Kx))
    def step(self,F):
        h=self.h
        b,i=self.apply(self.v,self.u,self.Mb,self.mi,1.)
        g,j=self.apply(self.q,self.x,self.Kb,self.ki,self.ks)
        rb=2*b/h-g+self.P@F;ri=2*i/h-j+self.F@F
        vm=cho_solve(self.fac,rb-self.A.T@np.sum(self.C*ri/self.Hi,axis=1))
        um=(ri-self.C*(self.A@vm)[:,None])/self.Hi
        db,di=self.apply(vm,um,self.Db,self.di,self.ds)
        obs=self.P.T@vm+np.einsum('wip,wi->p',self.F,um)
        loss=h*float(vm@db+np.sum(um*di));work=h*float(F@obs)
        self.q+=h*vm;self.x+=h*um;self.v=2*vm-self.v;self.u=2*um-self.u
        return obs,work,loss
    def matrices(self):
        # Independent dense assembly from original physical wire matrices.
        n=self.n;size=n+self.nw*self.partials;ports=self.P.shape[1]
        M=np.zeros((size,size));K=M.copy();D=M.copy();P=np.zeros((size,ports))
        M[:n,:n]=np.eye(n);K[:n,:n]=np.diag(self.k);D[:n,:n]=self.D
        P[:n]=self.P
        for j,w in enumerate(self.wires):P[:n,w.port]-=w.P[0]*self.A[j]
        for j,w in enumerate(self.wires):
            ids=np.arange(n+j*self.partials,n+(j+1)*self.partials)
            T=np.zeros((len(w.M),size));T[0,:n]=self.A[j];T[1:,ids]=w.U[:,:self.partials]
            M+=T.T@w.M@T;K+=T.T@w.K@T;D+=T.T@w.D@T;P[:,w.port]+=T.T@w.P
        return M,K,D,P
    def transfer(self,freq):
        Y=[]
        for f in freq:
            s=2j*np.pi*f;z=self.ks+s*self.ds+s*s
            c=self.ki+s*self.di+s*s*self.mi
            H=self.Kb+s*self.Db+s*s*self.Mb-self.A.T@(np.sum(c*c/z,axis=1)[:,None]*self.A)
            R=self.P-self.A.T@np.sum((c/z)[:,:,None]*self.F,axis=1)
            b=np.linalg.solve(H,R);i=(self.F-c[:,:,None]*(self.A@b)[:,None,:])/z[:,:,None]
            Y.append(s*(self.P.T@b+np.einsum('wip,wiq->pq',self.F,i)))
        return np.stack(Y)

def proof(a,steps=192):
    M,K,D,P=a.matrices();h=a.h
    # Energy-equilibrated independent dense midpoint.
    scale=1/np.sqrt(np.diag(M));H=2*M/h+D+h*K/2;fac=cho_factor(H*(scale[:,None]*scale[None,:]))
    q=np.zeros(len(M));v=q.copy();work=loss=peak=energy=state=observer=ledger=0.
    for t in range(steps):
        F=np.zeros(P.shape[1]);F[:min(4,len(F))]=np.sin(.11*t+np.arange(min(4,len(F))))*(t<steps//2)
        o,w,l=a.step(F)
        vm=scale*cho_solve(fac,scale*(2*M@v/h-K@q+P@F))
        q+=h*vm;v=2*vm-v
        ref=P.T@vm;wl=h*float(F@ref);ll=h*float(vm@D@vm)
        W=np.r_[a.q,a.x.ravel()];V=np.r_[a.v,a.u.ravel()]
        E=.5*float(v@M@v+q@K@q);dE=.5*float((V-v)@M@(V-v)+(W-q)@K@(W-q))
        work+=w;loss+=l;peak=max(peak,E,abs(work),loss)
        energy=max(energy,abs(a.energy()+loss-work)/max(peak,1e-30))
        state=max(state,np.sqrt(max(dE,0.)/max(E,peak*1e-12,1e-30)))
        observer=max(observer,np.linalg.norm(o-ref)/max(np.linalg.norm(ref),1e-12))
        ledger=max(ledger,abs(w-wl)/max(peak,1e-30),abs(l-ll)/max(peak,1e-30))
    gate=bool(max(energy,state,observer,ledger)<=1e-6)
    return dict(gate=gate,energyRelative=energy,stateEnergyRelative=state,observerRelative=observer,ledgerRelative=ledger,
        coordinates=len(M),steps=steps)

def load(root,scale):
    raw=(root/'frozen_wire_ports.json').read_bytes();f=json.loads(raw)
    d=json.loads((root/'wire_port_enrichment.json').read_text());s=d['summary'];keys=[45,48,60,64]
    expected=dict(gate=True,reductionGate=True,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,
        selectedRank=80,selectedExtra=8,wires=10,keys=keys,selectionUsedValidation=False,acousticLoadIncluded=False,timeDomainReady=False)
    if any(s.get(k)!=v for k,v in expected.items()) or d['frozenSha256']!=hashlib.sha256(raw).hexdigest() or f['scaleSha256']!=hashlib.sha256(scale.read_bytes()).hexdigest():raise ValueError('invalid wire source')
    if max(s[k] for k in ('trainingMaximum','innerMaximum','validationMaximum'))>.05:raise ValueError('unapproved reduction')
    if f['selectedRank']!=80 or f['keys']!=keys or len(set(f['wireIds']))!=10:raise ValueError('invalid wire identity')
    train=np.asarray(f['trainingHz'])
    if not np.allclose(train,development_grids()[0],rtol=1e-14,atol=0):raise ValueError('grid mismatch')
    z=read_npz(root,f['archive'],dict(stiffness=(80,),damping=(80,80),ports=(80,7),physicalLift=(1386,80),wirePorts=(10,80)),train)
    rows={x['key']:x for x in json.loads(scale.read_text())['rows']};wires=[]
    for name in f['wireIds']:
        key=int(name.split('-')[0][1:]);wires.append(Wire(rows[key],128,0,keys.index(key),name))
    for key in keys:
        ids=[w.id for w in wires if w.port==keys.index(key)]
        if set(ids)!={f'k{key}-s{i+1}' for i in range(rows[key]['count'])}:raise ValueError('wire count mismatch')
    return z,wires,hashlib.sha256(raw).hexdigest()

def timing(make,rate,n):
    a=make(rate,n);F=np.zeros(a.P.shape[1]);F[0]=1.;times=[];W=L=peak=err=0.
    for _ in range(32):
        t=time.perf_counter_ns()
        for j in range(64):
            _,w,l=a.step(F);W+=w;L+=l
        times.append((time.perf_counter_ns()-t)/1000);E=a.energy();peak=max(peak,E,abs(W),L);err=max(err,abs(E+L-W))
    return dict(partials=n,sampleRate=rate,medianUsPerSample=float(np.median(times)/64),overruns=sum(v>64e6/rate for v in times),
        energyRelative=err/max(peak,1e-30))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale);k,D,P,A=(z[x] for x in ('stiffness','damping','ports','wirePorts'))
    make=lambda r,n:CoupledWire(k,D,P,A,wires,r,n)
    train,inner,_=development_grids();base=np.geomspace(30,500,16);valid=base[:-1]**.125*base[1:]**.875
    m=dict(M=np.eye(80),K=np.diag(k),D=D,P=P)
    def ref(freq):
        out=[]
        for f in freq:
            y,_,audit=harmonic_reference(m,A,wires,np.zeros((80,80)),np.zeros((1,80)),f)
            if not audit['gate']:raise ValueError('harmonic reference failed')
            out.append(y)
        return np.stack(out)
    f=np.sort(np.r_[train,inner]);Y=ref(f);rows=[]
    for n in (8,16,32,64,128):
        x=make(48000,n);e=comparison(x.transfer(f),Y)
        rows.append(dict(partials=n,trainingMaximum=e['maximum']))
    if rows[-1]['trainingMaximum']>1e-8:raise ValueError('full wire transfer mismatch')
    selected=min((v for v in rows if v['trainingMaximum']<=.05),key=lambda v:v['partials'])
    n=selected['partials'];a.out.mkdir(parents=True,exist_ok=True)
    frozen=dict(selected=selected,candidates=rows,sourceFrozenSha256=sha,trainingHz=f.tolist(),plannedValidationHz=valid.tolist())
    raw=json.dumps(frozen,indent=2,allow_nan=False).encode();(a.out/'frozen_wire_midpoint.json').write_bytes(raw)
    V=ref(valid);err=comparison(make(48000,n).transfer(valid),V)
    proofs=[dict(sampleRate=r,partials=n,**proof(make(r,n))) for r in (48000,96000)]
    # Full-size algebraic proof at 48 kHz, even if reduced interiors selected.
    if n!=128:proofs.append(dict(sampleRate=48000,partials=128,**proof(make(48000,128),64)))
    bench=[timing(make,r,n) for r in (48000,96000)]
    gate=all(v['gate'] for v in proofs) and all(v['energyRelative']<=1e-6 for v in bench)
    summary=dict(gate=gate,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,structureRank=80,wires=10,
        selectedPartials=n,trainingMaximum=selected['trainingMaximum'],validationMaximum=err['maximum'],
        fullWireReplayMaximum=rows[-1]['trainingMaximum'],interiorReductionGate=bool(err['maximum']<=.05),
        maximumEnergyError=max(v['energyRelative'] for v in proofs+bench),maximumStateError=max(v['stateEnergyRelative'] for v in proofs),
        selectionUsedValidation=False,acousticLoadIncluded=False,hammerContactIncluded=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'wire_midpoint.json').write_text(json.dumps(dict(summary=summary,validation=err,proof=proofs,benchmark=bench,
        frozenSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_WIRE_MIDPOINT_GATE '+json.dumps(summary),flush=True)
    for v in rows:print('G3_WIRE_MIDPOINT_CASE '+json.dumps(v),flush=True)
    for v in bench:print('G3_WIRE_MIDPOINT_BENCH '+json.dumps(v),flush=True)
    if not gate:raise ValueError('wire midpoint proof failed')
if __name__=='__main__':main()

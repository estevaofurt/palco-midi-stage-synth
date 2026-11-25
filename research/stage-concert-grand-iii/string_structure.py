"""G3.05g exact frequency-domain condensation of fixed-front string interiors.
No local rear loads; all selected unison wires share the structural rear coordinate.
Condensation is algebraic, not a reduced acoustic or time-domain engine.
"""
import numpy as np
from scipy.linalg import eigh,cholesky,solve,solve_triangular
from structural_response import congruence,symmetric
from string_ports import element
from duplex_diagnostic import LOSS

class Wire:
    def __init__(self,row,N,rear,port,wireId):
        A,B,C=element(row,N);self.M=A[1:,1:];self.K=B[1:,1:];self.P=C[1:]
        self.D=2*(LOSS['mainSigma0PerS']*self.M+LOSS['mainSigma2S']*self.K)
        self.rear=rear;self.port=port;self.id=wireId
        w2,U=eigh(self.K[1:,1:],self.M[1:,1:]);assert min(w2)>0
        self.w2=w2;self.U=U
        self.m=U.T@self.M[1:,0];self.k=U.T@self.K[1:,0]
        self.d=U.T@self.D[1:,0];self.p=U.T@self.P[1:]
        self.gamma=2*(LOSS['mainSigma0PerS']+LOSS['mainSigma2S']*w2)
    def condense(self,w):
        z=self.K[0,0]-w*w*self.M[0,0]+1j*w*self.D[0,0]
        b=self.k-w*w*self.m+1j*w*self.d
        d=self.w2-w*w+1j*w*self.gamma
        invb=b/d;invp=self.p/d
        return z-b@invb,self.P[0]-b@invp,self.p@invp,invb,invp
    def recover(self,x,force,invb,invp):
        q=invp[:,None]*force[None,:]-invb[:,None]*x[None,:]
        return np.vstack([x,self.U@q])

def setup(structure,centers,rows,keys,sub,N):
    n=len(structure['M']);ports=len(keys)+3
    P=np.zeros((n,ports))
    # Last three ports: two structure force ports and plate observation/force.
    P[:,len(keys):]=structure['P'][:,[0,2,4]]
    wires=[];labels=[f'hammer-{k}' for k in keys]+['bass-bridge','treble-bridge','plate']
    offset=structure['plateDofs']+structure['rimDofs']
    for j,section in enumerate(('bass','treble')):
        center=centers[section]
        for k in keys:
            if k not in center['keys']:continue
            rear=offset+2*sub*center['keys'].index(k)
            for i in range(rows[k]['count']):
                wires.append(Wire(rows[k],N,rear,keys.index(k),f'k{k}-s{i+1}'))
        offset+=structure['bridgeDofs'][j]
    assert offset==n and len(wires)==sum(rows[k]['count'] for k in keys)
    return P,wires,labels

def response(M,K,D,P,wires,freq):
    M,_=symmetric(M);K,_=symmetric(K);D,_=symmetric(D)
    n=len(M);p=P.shape[1];Y=[];records=[]
    s=1/np.sqrt(np.diag(M));W=s[:,None]*s[None,:]
    M=M*W;K=K*W;D=D*W;P=P*s[:,None]
    for f in freq:
        w=2*np.pi*f;assert w>0
        # Base physical structural matrices, scaled by mass; add exact Schur terms.
        rhs=P.astype(complex);feed=np.zeros((p,p),complex)
        extra=np.zeros(n,complex);pre=np.zeros(n);local=[]
        for wire in wires:
            z,r,h,b,c=wire.condense(w);j=wire.rear;i=wire.port
            extra[j]+=z*s[j]**2;rhs[j,i]+=r*s[j];feed[i,i]+=h
            pre[j]+=(wire.K[0,0]+w*w*wire.M[0,0]+w*wire.D[0,0])*s[j]**2
            local.append((wire,b,c))
        L=cholesky(K+w*w*M+w*D+np.diag(pre),lower=True)
        G=congruence(L,K)-congruence(L,w*w*M)+1j*congruence(L,w*D)
        # Complex symmetric, not Hermitian, congruence for condensed impedance.
        idx=np.flatnonzero(extra)
        if len(idx):
            E=np.zeros((n,len(idx)));E[idx,np.arange(len(idx))]=1.
            E=solve_triangular(L,E,lower=True)
            G+=(E*extra[idx])@E.T
        R=solve_triangular(L,rhs,lower=True);v=solve(G,R)
        x=solve_triangular(L.T,v,lower=False)
        H=rhs.T@x+feed;Z=1j*w*H
        # Independent physical force/velocity power audit after reconstructing all wire states.
        expected=w*w*(x.conj().T@D@x)
        force=np.eye(p);residual=(K-w*w*M+1j*w*D)@x-P
        internal=0.;observation=P.T@x
        for wire,b,c in local:
            j=wire.rear;i=wire.port
            q=wire.recover(s[j]*x[j],force[i],b,c)
            expected+=w*w*(q.conj().T@wire.D@q)
            z=(wire.K-w*w*wire.M+1j*w*wire.D)@q-wire.P[:,None]*force[i]
            residual[j]+=s[j]*z[0]
            internal=max(internal,float(np.linalg.norm(z[1:])/max(np.linalg.norm(wire.P),1e-30)))
            observation[i]+=wire.P@q
        herm=(Z+Z.conj().T)/2
        row=dict(frequencyHz=float(f),reciprocity=float(np.linalg.norm(Z-Z.T)/max(np.linalg.norm(Z),1e-30)),
           passivityMinRelative=float(min(np.linalg.eigvalsh(herm))/max(np.linalg.norm(herm),1e-30)),
           powerRelative=float(np.linalg.norm(herm-expected)/max(np.linalg.norm(herm),np.linalg.norm(expected),1e-30)),
           structuralResidual=float(np.linalg.norm(residual)/max(np.linalg.norm(rhs),1e-30)),
           internalResidual=internal,observationRelative=float(np.linalg.norm(H-observation)/max(np.linalg.norm(H),1e-30)),
           scaledResidual=float(np.linalg.norm(G@v-R)/max(np.linalg.norm(R),1e-30)))
        Y.append(Z);records.append(row)
    summary={k:(min if k=='passivityMinRelative' else max)(q[k] for q in records) for k in records[0] if k!='frequencyHz'}
    summary['gate']=summary['reciprocity']<=1e-8 and summary['passivityMinRelative']>=-1e-8 and summary['powerRelative']<=1e-6 and summary['structuralResidual']<=1e-5 and summary['internalResidual']<=1e-5 and summary['observationRelative']<=1e-8 and summary['scaledResidual']<=1e-8
    return np.array(Y),summary,records

def full_reference(M,K,D,P,wires):
    """Direct full assembly, only for small regression fixtures."""
    n=len(M);size=n+sum(len(w.M)-1 for w in wires);p=P.shape[1]
    A=np.zeros((size,size));B=np.zeros_like(A);C=np.zeros_like(A);F=np.zeros((size,p))
    A[:n,:n]=M;B[:n,:n]=K;C[:n,:n]=D;F[:n]=P
    start=n
    for w in wires:
        ids=np.r_[w.rear,np.arange(start,start+len(w.M)-1)];start+=len(w.M)-1
        for x,z in ((A,w.M),(B,w.K),(C,w.D)):x[np.ix_(ids,ids)]+=z
        F[ids,w.port]+=w.P
    return A,B,C,F

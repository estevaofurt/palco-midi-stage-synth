"""G3.04b: centerline bridge and reciprocal load-free string assembly.
Vertical scalar model, one representative wire per selected note.
"""
import numpy as np
from scipy.linalg import eigh
from continuous_bridge import build
from string_ports import element
from duplex_string import Decay
from duplex_diagnostic import LOSS
def centerline(nodes):
    groups={}
    for n in nodes:groups.setdefault(n['key'],[]).append(n)
    keys=sorted(groups);xyz=np.array([np.mean([n['xyzM'] for n in groups[k]],axis=0) for k in keys])
    offsets={n['wireId']:(np.asarray(n['xyzM'])-xyz[i]).tolist() for i,k in enumerate(keys) for n in groups[k]}
    edges=np.diff(xyz,axis=0);length=np.linalg.norm(edges,axis=1)
    assert np.all(length>0)
    u=edges/length[:,None];angles=np.degrees(np.arccos(np.clip(np.sum(u[:-1]*u[1:],axis=1),-1,1)))
    return dict(keys=keys,xyz=xyz,offsets=offsets,lengthM=float(sum(length)),maxTurnDeg=float(max(angles)),turnsOver45=int(sum(angles>45)),
                maxOffsetM=max(float(np.linalg.norm(v)) for v in offsets.values()))
def assemble(center,rows,keys,sub,N,cfg,section):
    mat=cfg['material'];sec=cfg['section'][section];fix=cfg['fixture']
    b=build(center['xyz'],sub,mat['densityKgM3'],mat['youngAlongPa'],sec['widthM'],sec['heightM'],fix['foundationNperM2'])
    nb=len(b['M']);size=nb+N*len(keys);M=np.zeros((size,size));K=np.zeros_like(M)
    M[:nb,:nb]=b['M'];K[:nb,:nb]=b['K']+b['foundation']
    P=np.zeros((size,2*len(keys)));parts=[]
    parts.append(('bridgeFixture',np.arange(nb),b['M'],b['K']+b['foundation'],fix['massDampingPerS']*b['M']+fix['stiffnessDampingS']*(b['K']+b['foundation'])))
    for j,key in enumerate(keys):
        rr=rows[key];A,B,C=element(rr,N);A=A[1:,1:];B=B[1:,1:];C=C[1:] # front fixed
        rear=b['attachmentDofs'][center['keys'].index(key)]
        ids=np.r_[rear,np.arange(nb+j*N,nb+(j+1)*N)]
        M[np.ix_(ids,ids)]+=A;K[np.ix_(ids,ids)]+=B
        P[ids,j]=C;P[rear,len(keys)+j]=1.
        D=2*(LOSS['mainSigma0PerS']*A+LOSS['mainSigma2S']*B)
        parts.append((str(key),ids,A,B,D))
    return M,K,P,parts,b
class Coupled:
    def __init__(self,center,rows,keys,sub,N,cut,sr,cfg,section):
        M,K,P,self.parts,self.bridge=assemble(center,rows,keys,sub,N,cfg,section)
        w2,U=eigh(K,M);assert min(w2)>0
        keep=np.sqrt(w2)/(2*np.pi)<=cut;self.U=U[:,keep];self.w2=w2[keep];self.P=self.U.T@P;self.h=1/sr
        w=np.sqrt(self.w2);h=self.h;self.w=w;self.c=np.cos(w*h);self.s=np.sin(w*h)
        self.G=2*np.sin(w*h/2)**2/self.w2;self.J=self.s/w
        self.q=np.zeros_like(w);self.v=np.zeros_like(w);self.decays=[];self.losses={}
        for name,i,A,B,D in self.parts:
            W=self.U[i,:];self.decays.append((name,Decay(W.T@D@W,h/2)));self.losses[name]=0.
    def position(self):return self.P.T@self.q
    def energy(self):return .5*float(self.v@self.v+(self.w2*self.q)@self.q)
    @property
    def loss(self):return sum(self.losses.values())
    def step(self,F):
        for name,d in self.decays:self.v,L=d.step(self.v);self.losses[name]+=L
        q=self.q.copy();f=self.P@np.asarray(F)
        dq=(self.c-1)*q+self.J*self.v+self.G*f
        self.q=q+dq;self.v=-self.w*self.s*q+self.c*self.v+self.J*f
        for name,d in reversed(self.decays):self.v,L=d.step(self.v);self.losses[name]+=L
        return float(np.asarray(F)@(self.P.T@dq))
    def partition(self):
        q=self.U@self.q;v=self.U@self.v
        out={name:.5*float(v[i]@A@v[i]+q[i]@B@q[i]) for name,i,A,B,D in self.parts}
        assert min(out.values())>=-1e-15 and abs(sum(out.values())-self.energy())<=max(1e-12,self.energy()*1e-7)
        return out

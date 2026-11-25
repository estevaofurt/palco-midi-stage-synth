"""One common moving rear boundary for a unison group, vertical linear motion.
The support mass, spring and damper are assembled once, not once per wire.
"""
import numpy as np
from scipy.linalg import eigh
from moving_termination import matrices
def assemble(r,N,load,tensionOffsets):
    n=r['count']
    if len(tensionOffsets)!=n or n not in (1,2,3):raise ValueError('unison domain')
    size=1+n*N;M=np.zeros((size,size));K=np.zeros_like(M);P=np.zeros((size,n+1))
    M[0,0]=load['massKg'];K[0,0]=load['stiffnessNm'];P[0,-1]=1.
    parts=[]
    for i,offset in enumerate(tensionOffsets):
        # Approximate detune from tension, NOT measured or final pitch offsets.
        rr=dict(r,tensionPerStringN=r['tensionPerStringN']*2**(2*offset/1200))
        A,B,C=matrices(rr,N,load['massKg'],0.)
        A[0,0]-=load['massKg']
        ids=np.r_[0,np.arange(1+i*N,1+(i+1)*N)]
        M[np.ix_(ids,ids)]+=A;K[np.ix_(ids,ids)]+=B;P[ids,i]=C[:,0]
        parts.append((ids,A,B))
    return M,K,P,parts
class SharedUnison:
    def __init__(self,r,N,cut,sr,load,offsets):
        M,K,P,self.parts=assemble(r,N,load,offsets)
        w2,U=eigh(K,M);assert np.all(w2>0)
        mask=np.sqrt(w2)/(2*np.pi)<=cut
        self.w2=w2[mask];self.U=U[:,mask];self.P=self.U.T@P
        self.h=1/sr;self.cdrag=load['dampingNsm'];self.load=load
        w=np.sqrt(self.w2);h=self.h
        self.c=np.cos(w*h);self.s=np.sin(w*h);self.w=w
        self.G=2*np.sin(w*h/2)**2/self.w2;self.J=self.s/w
        self.q=np.zeros_like(w);self.v=np.zeros_like(w);self.loss=0.
        self.H=(self.P.T*self.G)@self.P;self.p=self.P[:,-1];self.den=1+self.cdrag*self.H[-1,-1]/h
        assert np.max(abs(self.H-self.H.T))<1e-12 and self.den>=1
    def position(self):return self.P.T@self.q
    def energy(self):return .5*float(self.v@self.v+(self.w2*self.q)@self.q)
    def step(self,F):
        F=np.asarray(F,dtype=float);q=self.q.copy()
        d=(self.c-1)*q+self.J*self.v
        free=d+self.G*(self.P@F)
        drag=self.cdrag/self.h*float(self.p@free)/self.den
        f=self.P@F-self.p*drag
        dq=d+self.G*f
        self.q=q+dq;self.v=-self.w*self.s*q+self.c*self.v+self.J*f
        dp=self.P.T@dq;loss=drag*float(dp[-1]);self.loss+=loss
        assert loss>=-1e-15
        return float(F@dp)
    def partition(self):
        x=self.U@self.q;v=self.U@self.v
        values=[.5*float(v[i]@A@v[i]+x[i]@B@x[i]) for i,A,B in self.parts]
        load=.5*(self.load['massKg']*v[0]**2+self.load['stiffnessNm']*x[0]**2)
        assert min(values)>=-1e-15 and abs(sum(values)+load-self.energy())<max(1e-12,self.energy()*1e-7)
        return values,float(load)

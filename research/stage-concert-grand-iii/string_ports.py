"""G3.03g: two-ended string element and removable diagnostic loads.
Physical coordinates [front translation, rear translation, normalized sines].
Loads are not part of the element; no acoustic calibration.
"""
import math
import numpy as np
from scipy.linalg import eigh
from wound_modes import mass_matrix,stiffness
from duplex_string import Decay

def element(r,N,width=.005):
    L=r['lengthM'];T=r['tensionPerStringN'];EI=r['bendingNm2'];s=r['hammerPositionM']
    if N<8 or not 0<width<=2*min(s,L-s):raise ValueError('segment domain')
    n=np.arange(1,N+1,dtype=float);k=n*np.pi/L;norm=math.sqrt(2/L)
    mu=r['linearDensityKgM'];core=r['coreMassPerM']
    if r['wrapLayers']:
        a,b=r['windingIntervalM'];extra=(mu-core)*L/(b-a)
        M0=mass_matrix(L,core,extra,a,b,N);pieces=[(0.,L,core),(a,b,extra)]
    else:M0=mu*np.eye(N);pieces=[(0.,L,mu)]
    M=np.zeros((N+2,N+2));M[2:,2:]=M0
    def primitives(x):
        right=(-x*np.cos(k*x)/k+np.sin(k*x)/k**2)*norm/L
        total=-norm*np.cos(k*x)/k
        return np.stack((total-right,right))
    for a,b,d in pieces:
        I0=b-a;I1=(b*b-a*a)/(2*L);I2=(b**3-a**3)/(3*L**2)
        M[:2,:2]+=d*np.array([[I0-2*I1+I2,I1-I2],[I1-I2,I2]])
        M[:2,2:]+=d*(primitives(b)-primitives(a))
    M[2:,:2]=M[:2,2:].T
    K=np.zeros_like(M);K[:2,:2]=T/L*np.array([[1.,-1.],[-1.,1.]])
    K[2:,2:]=np.diag(stiffness(L,EI,T,N))
    P=np.r_[1-s/L,s/L,norm*np.sin(k*s)*np.sinc(n*width/(2*L))]
    return M,K,P

def assemble(r,N,frontRatio,rearRatio,frontLoad,rearLoad):
    if not 0<=frontRatio<=1 or not 0<=rearRatio<=1:raise ValueError('duplex ratio')
    if r['wrapLayers'] and (frontRatio or rearRatio):raise ValueError('wound duplex unspecified')
    if frontLoad is None and frontRatio:raise ValueError('front support must be active')
    active=frontLoad is not None
    nends=2 if active else 1
    labels=['hammer','front','rear'] if active else ['hammer','rear']
    size=nends+N*(1+int(frontRatio>0)+int(rearRatio>0))
    M=np.zeros((size,size));K=np.zeros_like(M);P=np.zeros((size,len(labels)));parts=[];supports=[]
    rear=nends-1
    for idx,load,name in [(0,frontLoad,'front'),(rear,rearLoad,'rear')]:
        if load is None:continue
        if min(load['massKg'],load['stiffnessNm'],load['dampingNsm'])<0:raise ValueError('passive load required')
        M[idx,idx]+=load['massKg'];K[idx,idx]+=load['stiffnessNm'];P[idx,labels.index(name)]=1.
        supports.append((idx,load,name))
    # Rear is an exposed interface even if no diagnostic load is installed.
    P[rear,labels.index('rear')]=1.
    offset=nends
    def segment(rr,ends,name,hammer=False):
        nonlocal offset
        A,B,C=element(rr,N,.005 if hammer else min(.005,rr['lengthM']/2))
        ids=np.r_[ends,np.arange(offset,offset+N)];offset+=N
        keep=ids>=0;ids=ids[keep];A=A[np.ix_(keep,keep)];B=B[np.ix_(keep,keep)]
        M[np.ix_(ids,ids)]+=A;K[np.ix_(ids,ids)]+=B
        if hammer:P[ids,0]=C[keep]
        parts.append((name,ids,A,B))
    segment(r,[0 if active else -1,rear],'main',True)
    for ratio,idx,name in [(frontRatio,0,'frontDuplex'),(rearRatio,rear,'rearDuplex')]:
        if ratio:segment(dict(r,lengthM=r['lengthM']*ratio,hammerPositionM=r['lengthM']*ratio/2),[-1,idx],name)
    return M,K,P,parts,supports,labels

class PortString:
    def __init__(self,r,N,cut,sr,frontRatio,rearRatio,frontLoad,rearLoad,loss):
        M,K,P,self.parts,self.supports,self.labels=assemble(r,N,frontRatio,rearRatio,frontLoad,rearLoad)
        w2,U=eigh(K,M);assert np.all(w2>0),'fixture must constrain rigid translation'
        keep=np.sqrt(w2)/(2*np.pi)<=cut;self.U=U[:,keep];self.w2=w2[keep];self.P=self.U.T@P
        self.h=1/sr;w=np.sqrt(self.w2);h=self.h
        self.c=np.cos(w*h);self.s=np.sin(w*h);self.w=w;self.G=2*np.sin(w*h/2)**2/self.w2;self.J=self.s/w
        self.q=np.zeros_like(w);self.v=np.zeros_like(w);self.decays=[];self.losses={}
        for name,ids,A,B in self.parts:
            W=self.U[ids,:]
            D=2*(loss['mainSigma0PerS']*A+loss['mainSigma2S']*B) if name=='main' else 2*loss['duplexSigmaPerS']*A
            self.decays.append((name,Decay(W.T@D@W,h/2)));self.losses[name]=0.
        # Support loss is distinct from string losses; exact rank-one velocity subflow.
        for idx,l,name in self.supports:
            p=self.U[idx,:];D=l['dampingNsm']*np.outer(p,p)
            self.decays.append((name+'Support',Decay(D,h/2)));self.losses[name+'Support']=0.
    def energy(self):return .5*float(self.v@self.v+(self.w2*self.q)@self.q)
    @property
    def loss(self):return sum(self.losses.values())
    def position(self):return self.P.T@self.q
    def decay(self,items):
        for name,d in items:
            self.v,L=d.step(self.v);self.losses[name]+=L
    def step(self,F):
        F=np.asarray(F,dtype=float)
        if F.shape!=(len(self.labels),):raise ValueError('port forces')
        self.decay(self.decays);q=self.q.copy();f=self.P@F
        dq=(self.c-1)*q+self.J*self.v+self.G*f
        self.q=q+dq;self.v=-self.w*self.s*q+self.c*self.v+self.J*f
        self.decay(reversed(self.decays))
        return float(F@(self.P.T@dq))
    def partition(self):
        q=self.U@self.q;v=self.U@self.v
        out={name:.5*float(v[i]@A@v[i]+q[i]@B@q[i]) for name,i,A,B in self.parts}
        for idx,l,name in self.supports:out[name+'Support']=.5*float(l['massKg']*v[idx]**2+l['stiffnessNm']*q[idx]**2)
        assert min(out.values())>=-1e-15 and abs(sum(out.values())-self.energy())<=max(1e-12,self.energy()*1e-7)
        return out

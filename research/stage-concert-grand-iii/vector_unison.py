"""Vector unison with one common support displacement per transverse axis."""
import numpy as np
import math
from shared_unison import SharedUnison
class VectorUnison:
    def __init__(self,r,N,cut,sr,load,angle,offsets):
        if not math.isfinite(angle):raise ValueError('angle')
        a,b=math.cos(angle),math.sin(angle);self.R=np.array([[a,-b],[b,a]])
        self.n=r['count']
        self.axes=[SharedUnison(r,N,cut,sr,dict(massKg=load['massKg'],stiffnessNm=k,dampingNsm=c),offsets) for k,c in zip(load['stiffnessNm'],load['dampingNsm'])]
        if len(self.axes)!=2:raise ValueError('two axes')
    def position(self):return np.stack([t.position() for t in self.axes],axis=1)@self.R.T
    def energy(self):return sum(t.energy() for t in self.axes)
    @property
    def loss(self):return sum(t.loss for t in self.axes)
    def step(self,F):
        F=np.asarray(F,dtype=float)
        if F.shape!=(self.n+1,2):raise ValueError('port shape')
        before=self.position();local=F@self.R
        work=sum(t.step(local[:,i]) for i,t in enumerate(self.axes))
        assert abs(work-float(np.sum(F*(self.position()-before))))<1e-12
        return work
    def partition(self):
        a,b=[t.partition() for t in self.axes]
        return [x+y for x,y in zip(a[0],b[0])],a[1]+b[1]

"""Two transverse polarizations with a rotated anisotropic rear load.
One physical wire, vector displacement. Principal-axis decomposition is exact
for isotropic transverse string operators and co-diagonal rear K/D.
No actual bridge geometry, no longitudinal motion or audio.
"""
import math
import numpy as np
from moving_termination import basis,Boundary
class PolarizedWire:
    def __init__(self,r,N,cut,sr,load,angle):
        # Coordinates order [vertical, lateral]; columns of R are principal axes.
        if not math.isfinite(angle):raise ValueError('angle')
        a=math.cos(angle);b=math.sin(angle);self.R=np.array([[a,-b],[b,a]])
        self.load=load;self.axes=[]
        for k,c in zip(load['stiffnessNm'],load['dampingNsm']):
            w,P=basis(r,N,cut,load['massKg'],k)
            self.axes.append(Boundary(w,P,sr,c))
        if len(self.axes)!=2:raise ValueError('two principal axes required')
    def energy(self):return sum(t.energy() for t in self.axes)
    @property
    def loss(self):return sum(t.loss for t in self.axes)
    def position(self):return np.stack([t.position() for t in self.axes],axis=1)@self.R.T
    def velocity(self):return np.stack([t.velocity() for t in self.axes],axis=1)@self.R.T
    def step(self,F):
        # rows: hammer and rear; columns: vertical and lateral
        F=np.asarray(F,dtype=float)
        if F.shape!=(2,2):raise ValueError('four conjugate force components')
        local=F@self.R;old=self.position()
        z=[t.step(local[:,i]) for i,t in enumerate(self.axes)]
        work=sum(q['work'] for q in z);loss=sum(q['loss'] for q in z)
        err=abs(float(np.sum(F*(self.position()-old)))-work)
        assert err<1e-12
        return dict(work=work,loss=loss,rotationWorkResidualJ=err)
    def load_energy(self):
        q=np.array([t.position()[1] for t in self.axes]);v=np.array([t.velocity()[1] for t in self.axes])
        return float(.5*(self.load['massKg']*(v@v)+np.asarray(self.load['stiffnessNm'])@(q*q)))

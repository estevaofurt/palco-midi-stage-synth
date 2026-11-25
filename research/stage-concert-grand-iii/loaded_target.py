"""Reciprocal scalar hammer contact adapter for a damped two-port boundary.
The rear port is passive and internal; a separate load for each wire, not a bridge.
"""
import numpy as np
from moving_termination import Boundary
class LoadedTarget:
    def __init__(self,w2,P,sr,load):
        self.b=Boundary(w2,P,sr,load['dampingNsm']);self.load=load;self.P=self.b.P[:,0]
        b=self.b
        self.H=float(b.H[0,0]-b.damp/b.h*b.H[0,1]**2/b.den)
        assert self.H>=0
    @property
    def q(self):return self.b.q
    @property
    def v(self):return self.b.v
    @property
    def loss(self):return self.b.loss
    def energy(self):return self.b.energy()
    def position(self):return float(self.b.position()[0])
    def free(self):
        b=self.b;dq=(b.c-1)*b.q+b.J*b.v;dp=b.P.T@dq
        drag=b.damp/b.h*dp[1]/b.den
        return self.position()+float(dp[0]-b.H[0,1]*drag)
    def step(self,F):return self.b.step([F,0.])['work']
    def load_energy(self):
        x=self.b.position()[1];v=self.b.velocity()[1]
        return .5*(self.load['massKg']*v*v+self.load['stiffnessNm']*x*x)

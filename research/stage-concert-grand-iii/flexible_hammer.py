"""Reduced free hammer head/shaft flexural fixture.
Two translating equivalent masses, one relative elastic mode, no fitted geometry.
Force conjugate to head displacement. Preserve original total effective mass.
"""
import math
import numpy as np
from modal_target import Target
class Hammer:
    def __init__(self,m,sr,speed,shaft=None):
        if not all(math.isfinite(x) for x in (m,sr,speed)) or m<=0 or sr<=0:raise ValueError('hammer domain')
        self.m=m;self.h=1/sr;self.x=0.;self.v=speed;self.flex=None
        self.H=self.h**2/(2*m)
        if shaft is not None:
            a=shaft['headMassFraction'];freq=shaft['relativeModeHz']
            if not 0<a<1 or not math.isfinite(freq) or freq<=0:raise ValueError('shaft domain')
            # r=head displacement minus rear equivalent mass displacement,
            # head = x_COM+(1-a)*r; modal q=sqrt(mu)*r.
            mu=m*a*(1-a);P=(1-a)/math.sqrt(mu)
            self.flex=Target(np.array([(2*math.pi*freq)**2]),np.array([P]),sr)
            self.H+=self.flex.H
    def position(self):return self.x+(self.flex.position() if self.flex else 0.)
    def velocity(self):return self.v+(float(self.flex.P@self.flex.v) if self.flex else 0.)
    def free(self):return self.x+self.h*self.v+(self.flex.free() if self.flex else 0.)
    def flex_energy(self):return self.flex.energy() if self.flex else 0.
    def energy(self):return .5*self.m*self.v*self.v+self.flex_energy()
    def step(self,F):
        old=self.position()
        self.x=self.x+self.h*self.v+self.h**2*F/(2*self.m)
        self.v+=self.h*F/self.m
        if self.flex:self.flex.step(F)
        return F*(self.position()-old)

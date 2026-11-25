"""Reduced reciprocal geometric nonlinearity, solid wire, fixed ends.
Two transverse fundamental amplitudes and axial second sine mode.
Not a full longitudinal basis or actual bridge interface.
"""
import numpy as np
import math
class AxialFixture:
    def __init__(self,r,sr,amplitude,angle=0.):
        if r['wrapLayers'] or sr<=0 or amplitude<=0:raise ValueError('solid wire fixture')
        L=r['lengthM'];a=math.pi/L;EA=202e9*math.pi*r['coreDiameterM']**2/4
        self.h=1/sr;self.mass=r['linearDensityKgM']*L/2;self.kt=(r['tensionPerStringN']*a*a+r['bendingNm2']*a**4)*L/2
        self.alpha=a*a/4;self.beta=2*a;self.EAL=EA*L
        self.q=np.array([amplitude*math.cos(angle),amplitude*math.sin(angle),0.]);self.v=np.zeros(3)
        self.kl=self.EAL*self.beta**2/2
        self.linear=np.array([self.kt,self.kt,self.kl])
    def strain(self,q):
        B=self.alpha*float(q[:2]@q[:2]);C=self.beta*q[2]+B
        return B,C
    def potential(self,q):
        B,C=self.strain(q)
        return .5*self.kt*float(q[:2]@q[:2])+.5*self.EAL*(B*B+.5*C*C)
    def energy(self):return .5*self.mass*float(self.v@self.v)+self.potential(self.q)
    def gradient(self,q,r):
        B,C=self.strain(q);D,E=self.strain(r);B=.5*(B+D);C=.5*(C+E)
        g=.5*self.kt*(q[:2]+r[:2])+self.EAL*(B+.5*C)*self.alpha*(q[:2]+r[:2])
        return np.r_[g,.5*self.EAL*C*self.beta]
    def step(self):
        q=self.q;h=self.h;m=self.mass
        # Discrete gradient: Delta V = g dot Delta q, exact algebra.
        # Precondition the implicit solve with the full linear part.
        A=h*h/(2*m);den=1+A*self.linear/2
        rhs=(q+h*self.v-A*self.linear*q/2)/den
        x=rhs.copy()
        for _ in range(30):
            nonlin=self.gradient(q,x)-.5*self.linear*(q+x)
            y=rhs-A*nonlin/den
            if np.max(abs(y-x))<=1e-16:
                x=y;break
            x=y
        else:raise ArithmeticError('discrete gradient iteration')
        g=self.gradient(q,x);res=float(np.max(abs(x-q-h*self.v+A*g)))
        assert res<=1e-14
        workerr=abs(self.potential(x)-self.potential(q)-float(g@(x-q)))
        self.q=x;self.v=self.v-h*g/m
        return workerr
    def axial_force(self):
        B,C=self.strain(self.q)
        # Dynamic rear axial stress resultant at x=L, pretension excluded.
        return self.EAL*self.beta/(2*math.pi)*(B+C)

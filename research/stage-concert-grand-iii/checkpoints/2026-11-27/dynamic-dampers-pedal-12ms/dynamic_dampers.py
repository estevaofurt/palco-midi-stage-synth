"""Nonnegative time-varying damping, no reset and no change to M or K.
Control coefficients sampled at step midpoint. No model of damper inertia.
"""
import numpy as np
from compact_mechanics import Operator, CompactSolve, CompactWet, midpoint

class Dampers:
    def __init__(self,open_D,wires):
        assert not np.any(open_D.a)
        self.base=open_D
        self.keys=np.array([w['key'] for w,*_ in wires]);self.maximum=np.array([2/np.count_nonzero(self.keys==k) for k in self.keys])
    def operator(self,closure):
        closure=np.asarray(closure,float)
        if closure.shape!=self.maximum.shape or not np.all((closure>=0)&(closure<=1)):raise ValueError('closure must be in [0,1]')
        b=self.base;a=self.maximum*closure
        return Operator(b.board+b.g.T@((.18**2*a)[:,None]*b.g),b.g,b.ids,b.d,b.c+.18*b.v*a[b.ids],b.v,a)
    def loss(self,op,v,h):
        b=self.base;y=v[80:];u=.18*(b.g@v[:80])+b.sum(b.v*y)
        return h*op.a*u*u

class DynamicWet(CompactWet):
    def __init__(self,c,e,Z,s,M,K,dampers,closure):
        self.dampers=dampers;self.closure=np.asarray(closure,float).copy();self.updates=0
        super().__init__(c,e,Z,s,M,K,dampers.operator(self.closure))
        self.Zb=self.Pb@(self.Aa@self.Wb-self.Ab@self.Xb)
    def set_closure(self,closure):
        closure=np.asarray(closure,float)
        if np.array_equal(closure,self.closure):return
        D=self.dampers.operator(closure)
        block=CompactSolve(midpoint(self.Ms,self.Ks,D,self.h,self.Zb))
        self.Ds,self.block,self.closure=D,block,closure.copy();self.updates+=1
    def step(self,f,reference=False):
        row=super().step(f,reference)
        row['damper_loss']=self.dampers.loss(self.Ds,row['v'],self.h)
        return row

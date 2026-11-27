"""Time-varying positive damping, preserving all mechanical/acoustic states.
Pedal and key commands are idealized damping controls, not action geometry.
"""
import numpy as np
from scipy.linalg import cholesky
from compact_mechanics import Operator, CompactSolve, CompactWet, midpoint

class Dampers:
    def __init__(self,free,wires,scale):
        if np.any(free.a):raise ValueError('requires fully lifted D')
        self.free=free;self.keys=np.array([w[0]['key'] for w in wires]);counts={r['key']:r['count'] for r in scale['rows']}
        self.maximum=np.array([2/counts[k] for k in self.keys]);self.allowed=set(self.keys)
    def fractions(self,held,pedal):
        held=set(held);pedal=float(pedal)
        if not held<=self.allowed or not 0<=pedal<=1:raise ValueError('invalid key or pedal')
        return np.array([0. if k in held else 1-pedal for k in self.keys])
    def operator(self,fractions):
        f=np.asarray(fractions,float)
        if f.shape!=self.maximum.shape or not np.isfinite(f).all() or np.any(f<0) or np.any(f>1):raise ValueError('invalid damper fractions')
        a=f*self.maximum;d=self.free
        board=d.board+d.g.T@((.18**2*a)[:,None]*d.g)
        cross=d.c+.18*d.v*a[d.ids]
        return Operator(board,d.g,d.ids,d.d,cross,d.v,a)

class DynamicWet(CompactWet):
    def __init__(self,c,e,Z,s,M,K,damper,held,pedal=0):
        self.damper=damper;self.fractions=damper.fractions(held,pedal)
        super().__init__(c,e,Z,s,M,K,damper.operator(self.fractions))
        self.Zb=self.Pb@(self.Aa@self.Wb-self.Ab@self.Xb)
    def command(self,held,pedal):
        f=self.damper.fractions(held,pedal)
        if np.array_equal(f,self.fractions):return False
        D=self.damper.operator(f)
        # Validate before replacing; neither reset nor acoustic step is called.
        S=D.schur();cholesky((S+S.T)/2,lower=True)
        block=CompactSolve(midpoint(self.Ms,self.Ks,D,self.h,self.Zb))
        self.Ds,self.block,self.fractions=D,block,f
        return True

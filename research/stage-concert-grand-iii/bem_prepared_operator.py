"""Reusable source quadrature for the unchanged analytic P1 BEM operator.
One immutable geometry snapshot and quadrature order per instance.
No target geometry, frequency or derivative result is cached.
"""
import numpy as np
from bem_p1_static_moments import source_quadrature,_operators
class PreparedOperator:
    def __init__(self,t,order):
        t=np.asarray(t,float)
        if t.ndim!=3 or t.shape[1:]!=(3,3) or not len(t) or not np.isfinite(t).all() or not isinstance(order,int) or isinstance(order,bool) or order<2:
            raise ValueError('invalid source quadrature')
        self._mesh=t.copy();self._mesh.setflags(write=False);self.order=order
        self._source=source_quadrature(self._mesh,order)
        for a in self._source:a.setflags(write=False)
        self.sourceBytes=sum(a.nbytes for a in self._source)
    def __call__(self,t,x,n,owner,k,order,derivative_only=False):
        if order!=self.order or not np.array_equal(t,self._mesh):
            raise ValueError('prepared source geometry or order changed')
        return _operators(self._mesh,x,n,owner,k,self._source,derivative_only)

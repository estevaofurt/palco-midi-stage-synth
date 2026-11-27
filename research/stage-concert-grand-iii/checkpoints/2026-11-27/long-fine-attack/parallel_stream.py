"""Parallel exact lag sum, private accumulators and deterministic final reduction."""
import numpy as np
from numba import njit,prange
from constant_stream import ConstantStream,accumulate

@njit(parallel=True)
def history_parallel(F,X0,X1,t,L,count,idx,sgn,groups):
    a=np.zeros((groups,1,X0.shape[2],X0.shape[3]),np.complex128)
    b=np.zeros((groups,X1.shape[1],X1.shape[2],X1.shape[3]),np.complex128)
    for j in prange(groups):
        lo=count*j//groups;hi=count*(j+1)//groups
        accumulate(a[j],b[j],F,X0,X1,t,L,hi-lo,lo+1,idx,sgn)
    y0=a[0].copy();y1=b[0].copy()
    for j in range(1,groups):
        y0+=a[j];y1+=b[j]
    return y0,y1

class ParallelStream(ConstantStream):
    def history(self):
        count=min(self.t,self.L-1)
        if count<128:return super().history()
        return self.decode(history_parallel(self.F,self.X0,self.X1,self.t,self.L,count,self.idx,self.sgn,4))

"""Full-lag circular fine reference: exact original spatial convolution."""
import numpy as np
from fine369 import FineStream
class RingFine(FineStream):
    def history_spec(self):
        n=min(self.t,self.L-1);y=np.zeros_like(self.X[0]);end=self.t%self.L;first=min(n,end)
        for j,count,x in [(0,first,self.X[end-first:end][::-1]),(first,n-first,self.X[self.L-(n-first):][::-1])]:
            if not count:continue
            f=self.F[:,1+j:1+j+count,0,0]
            for k in range(2):
                for a in (0,1):
                    xx=x[:,k^a,0];ff=f[a]
                    y[k,0].real+=np.einsum('lij,lij->ij',ff,xx.real)
                    y[k,0].imag+=np.einsum('lij,lij->ij',ff,xx.imag)
        return y

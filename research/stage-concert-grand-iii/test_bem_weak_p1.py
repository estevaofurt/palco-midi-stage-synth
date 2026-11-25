import unittest
import numpy as np
from test_exterior_bem import sphere
from bem_weak_p1 import assembly,fit
from bem_galerkin import assembly as constant
from bem_oversampled import audit,audit_targets
from split_radiation import relative
from exterior_bem import elements
class WeakP1Test(unittest.TestCase):
    def test_constant_subspace(self):
        t=sphere(.5,0);N=len(t);k=2*np.pi*80/343.
        v=lambda x,owner:np.ones((len(x),1))
        D,B=assembly(t,k,4,5,v);_,d,_=constant(t,k,4,5)
        np.testing.assert_allclose(B.reshape(N,3).sum(1),elements(t)[2],atol=1e-12)
        np.testing.assert_allclose(D.reshape(N,3,N,3).sum(axis=(1,3)),d,rtol=1e-9,atol=1e-11)
    def test_sphere(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        v=lambda x,owner:np.ones((len(x),1))
        q,r=fit(t,k,4,5,v);self.assertLess(r['weakResidual'],1e-10)
        x,n,w,owner=audit_targets(t)
        Z,P,rep=audit(t,q,v(x,owner),k,[[1.,0.,0.]],7)
        exact=4*np.pi*.5**2*1j*1.204*343*k/(2+1j*k)
        self.assertLess(abs(Z[0,0]-exact)/abs(exact),.25)
        self.assertLess(rep['powerRelative'],.15)
if __name__=='__main__':unittest.main()

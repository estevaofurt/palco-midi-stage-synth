import unittest,math
import numpy as np
from test_exterior_bem import sphere
from bem_weak_p1_refined import L5,W5,assembly,fit
from bem_weak_p1 import assembly as legacy
from bem_oversampled import AUDIT,audit_targets
from bem_linear import CHECK
from bem_p1_stream import audit
from exterior_bem import elements
from split_radiation import relative
class RefinedWeakTest(unittest.TestCase):
    def test_degree_five_and_independent_points(self):
        self.assertTrue(np.all(W5>0))
        for i in range(6):
            for j in range(6-i):
                for k in range(6-i-j):
                    exact=2*math.factorial(i)*math.factorial(j)*math.factorial(k)/math.factorial(i+j+k+2)
                    self.assertAlmostEqual(W5@(L5[:,0]**i*L5[:,1]**j*L5[:,2]**k),exact,places=13)
        for x in L5:self.assertFalse(any(np.allclose(x,y) for y in np.vstack([AUDIT,CHECK])))
    def test_tensor_equivalence(self):
        t=sphere(.5,0);k=2*np.pi*80/343.
        v=lambda x,o:np.c_[np.ones(len(x)),x[:,0]]
        D,B=assembly(t,k,4,5,v);d,b=legacy(t,k,4,5,v)
        np.testing.assert_allclose(D,d,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(B,b,rtol=1e-12,atol=1e-12)
    def test_symmetric_sphere(self):
        t=sphere(.5,1);k=2*np.pi*80/343.;v=lambda x,o:np.ones((len(x),1))
        q,r=fit(t,k,'symmetric5',6,v);self.assertLess(r['weakResidual'],1e-10)
        x,n,w,o=audit_targets(t);Z,P,rr=audit(t,q,v(x,o),k,[[1.,0.,0.]],7)
        exact=4*np.pi*.5**2*1j*1.204*343*k/(2+1j*k)
        self.assertLess(abs(Z[0,0]-exact)/abs(exact),.25)
        self.assertLess(rr['powerRelative'],.15)
if __name__=='__main__':unittest.main()

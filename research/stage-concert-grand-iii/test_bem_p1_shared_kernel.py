import unittest
import numpy as np
from test_exterior_bem import sphere
from bem_linear import COL,CHECK,targets,operators,fit as fit1
from bem_oversampled import TRAIN,fit as fitover
from bem_weak_p1 import assembly,fit as fitweak
from bem_weak_p1_refined import assembly as refined
from unittest.mock import patch
class SharedKernelTest(unittest.TestCase):
    def test_derivative_only_no_pressure_work(self):
        t=sphere(.5,1);x,n,w,o=targets(t,CHECK)
        for k in (0.,2*np.pi*150/343.):
            G,D=operators(t,x,n,o,k,5)
            with patch('bem_linear.self_integral',side_effect=AssertionError('pressure work executed')):
                g,d=operators(t,x,n,o,k,5,derivative_only=True)
            self.assertIsNone(g);np.testing.assert_array_equal(d,D)
    def test_solvers_keep_dense_reference(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        v=lambda x,o:np.c_[np.ones(len(x)),x[:,0]]
        for L,fit in ((COL,fit1),(TRAIN,fitover)):
            x,n,w,o=targets(t,L)
            q,r=fit(t,v(x,o),k,5);q0,r0=fit(t,v(x,o),k,5,derivative_only=False)
            np.testing.assert_allclose(q,q0,rtol=1e-12,atol=1e-12)
        D,B=assembly(t,k,3,5,v);d,b=assembly(t,k,3,5,v,derivative_only=False)
        np.testing.assert_array_equal(D,d);np.testing.assert_array_equal(B,b)
        dr,br=refined(t,k,3,5,v)
        np.testing.assert_array_equal(D,dr);np.testing.assert_array_equal(B,br)
        q,r=fitweak(t,k,3,5,v);q0,r0=fitweak(t,k,3,5,v,derivative_only=False)
        np.testing.assert_allclose(q,q0,rtol=1e-12,atol=1e-12)
if __name__=='__main__':unittest.main()

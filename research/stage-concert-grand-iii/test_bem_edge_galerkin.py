import unittest
import numpy as np
from exterior_bem import elements
from bem_edge_audit import edge_samples
from bem_edge_galerkin import rule,fit,assembly
from bem_p1_static_moments import fit as tensor_fit,operators
from bem_power_partition import integrate,partition
from bem_linear import far_gram
from test_exterior_bem import sphere
from split_radiation import relative
class EdgeGalerkinTest(unittest.TestCase):
    def test_rule_equivalence(self):
        t=sphere(.5,0);L,w=rule(4);x,W=edge_samples(t,4)
        np.testing.assert_allclose(np.einsum('qa,tad->tqd',L,t),x,atol=1e-14)
        np.testing.assert_allclose(elements(t)[2][:,None]*w,W,atol=1e-14)
        self.assertTrue(np.all(L>0) and np.all(w>0))
        np.testing.assert_allclose(w@L,np.ones(3)/3,atol=1e-14)
    def test_weak_rhs_and_sphere(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        v=lambda x,o:np.ones((len(x),1))
        D,B=assembly(t,k,3,5,v)
        np.testing.assert_allclose(B[:,0],np.repeat(elements(t)[2]/3,3),atol=1e-14)
        q,r=fit(t,k,3,5,v)
        self.assertLess(r['weakResidual'],1e-10)
        self.assertLess(relative(D@q,-B),1e-10)
        P,C,ar=integrate(t,q,v,k,5,6,operator=operators,sample_rule=edge_samples)
        F=1.204*343*k*k/(4*np.pi)*far_gram(t,q,k,order=24,surface_order=6)
        exact=4*np.pi*.5**2*1j*1.204*343*k/(2+1j*k)
        self.assertLess(abs(P[0,0]-exact)/abs(exact),.25)
        self.assertLess(partition(P,C,F)['computedWorkRelative'],.15)
    def test_static_finite(self):
        t=sphere(.5,0);v=lambda x,o:np.ones((len(x),1))
        q,r=fit(t,0.,3,4,v);qt,rt=tensor_fit(t,0.,4,4,v)
        self.assertTrue(np.isfinite(q).all() and np.isfinite(qt).all())
        self.assertLess(r['weakResidual'],1e-10)
if __name__=='__main__':unittest.main()

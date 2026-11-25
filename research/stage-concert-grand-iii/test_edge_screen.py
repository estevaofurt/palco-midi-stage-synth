import unittest
import numpy as np
from edge_screen import EdgeBasis,graded,operators,solve
from rigid_screen import geometry
class EdgeTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
    def test_quadrature_and_nesting(self):
        q,w=graded(self.poly,14);self.assertAlmostEqual(w.sum(),1.)
        b=EdgeBasis(self.poly,4);S=b.evaluate(q)[0]
        np.testing.assert_allclose(S.T@(w[:,None]*S),np.eye(15),atol=1e-10)
        np.testing.assert_allclose(S[:,:6],EdgeBasis(self.poly,2).evaluate(q)[0],atol=1e-10)
    def test_gradient_and_edge_scaling(self):
        b=EdgeBasis(self.poly,3);q=np.array([[.3,.4],[.7,.2]]);h=1e-6
        V,X,Y=b.evaluate(q)
        for d,g in [(np.array([h,0.]),X),(np.array([0.,h]),Y)]:
            np.testing.assert_allclose(g,(b.evaluate(q+d)[0]-b.evaluate(q-d)[0])/(2*h),rtol=1e-6,atol=1e-8)
        S=b.evaluate(np.array([[1e-6,.5],[4e-6,.5]]))[0]
        self.assertAlmostEqual(S[1,0]/S[0,0],2.,places=4)
    def test_operator_finite_and_power(self):
        local,o,A,n=geometry(self.poly,30,.24);b=EdgeBasis(local,3)
        k=1.5;W=operators(b,[k],10,18)[0]
        sources=np.array([[.4,.5,1.3],[.6,.5,-.7]])
        near,Z,r=solve(b,W,k,o,A,n,sources,np.array([[.6,.6,2.]]),2,16)
        self.assertTrue(np.isfinite(Z).all())
        self.assertLess(r['powerRelative'],.01,r)
        self.assertGreaterEqual(r['passivityMinRelative'],-1e-8,r)
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from shared_edge_quadrature import joint_samples,shared_pair,regular_pair,jac,align
class SharedEdgeTest(unittest.TestCase):
    def setUp(self):
        self.a=np.array([[0.,0.,0.],[1.,0.,0.],[.3,.8,0.]])
        self.b=np.array([[0.,0.,0.],[1.,0.,0.],[.6,0.,-.7]])
        self.n=np.array([0.,0.,1.])
        self.ones=lambda x:np.ones((len(x),1))
    def test_constant_measure(self):
        total=sum(w.sum() for x,y,w in joint_samples(self.a,self.b,8))
        self.assertAlmostEqual(total,jac(self.a)*jac(self.b)/4,places=12)
        self.assertTrue(np.allclose(align(self.a,self.b[[1,0,2]]),self.b))
    def test_static_sign_and_convergence(self):
        args=(self.a,self.b,self.ones,self.ones,self.n,[0.,2.])
        x=shared_pair(*args,12);y=shared_pair(*args,20)
        self.assertLess(x[0,0,0].real,0.)
        self.assertLess(np.linalg.norm(x-y)/np.linalg.norm(y),.01)
        self.assertTrue(np.isfinite(y).all())
    def test_regular_separated_limit(self):
        b=self.b.copy();b[:,2]-=.5
        # A joint transform remains a valid change of variables even if
        # the two edges are separated; compare independent tensor rule.
        args=(self.a,b,self.ones,self.ones,self.n,[0.,2.])
        x=shared_pair(*args,10);y=regular_pair(*args,14)
        np.testing.assert_allclose(x,y,rtol=1e-5,atol=1e-9)
if __name__=='__main__':unittest.main()

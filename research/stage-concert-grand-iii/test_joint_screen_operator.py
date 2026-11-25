import unittest
import numpy as np
from edge_screen import EdgeBasis,operators as directional,solve
from joint_screen_operator import operators,pair_samples,jac
from rigid_screen import geometry
from split_radiation import relative
class JointOperatorTest(unittest.TestCase):
    def test_pair_measure(self):
        a=np.array([[0.,0.],[1.,0.],[.4,.4]])
        b=np.array([[1.,0.],[1.,1.],[.4,.4]])
        c=np.array([[1.,1.],[0.,1.],[.4,.4]])
        for y,same in [(a,True),(b,False),(c,False)]:
            integral=sum(w.sum() for x,z,w in pair_samples(a,y,10,same))
            self.assertAlmostEqual(integral*(2 if same else 1),jac(a)*jac(y)/4,places=10)
    def test_static_and_harmonic(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,.8],[0.,.8]])
        local,o,A,n=geometry(poly,0,0);b=EdgeBasis(local,3)
        k=2*np.pi*80/343.;W,r=operators(b,[0.,k],14)
        self.assertLess(r['measureRelative'],1e-9)
        self.assertLess(r['reciprocity'],1e-12)
        self.assertGreater(min(np.linalg.eigvalsh(W[0].real)),0.)
        D=directional(b,[k],18,34)[0]
        self.assertLess(relative(W[1],D),.05)
        _,z,q=solve(b,W[1],k,o,A,n,np.array([[.4,.4,-.5]]),np.array([[.4,.4,.8]]),2,20)
        self.assertLess(q['powerRelative'],.01,q)
        self.assertTrue(np.isfinite(z).all())
if __name__=='__main__':unittest.main()

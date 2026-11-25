import unittest
import numpy as np
from rigid_screen import ScreenBasis,geometry,coupling,solve_screen
class ScreenTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
    def test_basis(self):
        b=ScreenBasis(self.poly,3);v,x,y=b.evaluate(np.array([[.3,.4]]));h=1e-6
        for d,g in [(np.array([h,0.]),x),(np.array([0.,h]),y)]:
            np.testing.assert_allclose(g,(b.evaluate([[.3+d[0],.4+d[1]]])[0]-b.evaluate([[.3-d[0],.4-d[1]]])[0])/(2*h),rtol=1e-7,atol=1e-8)
        np.testing.assert_allclose(b.evaluate(self.poly)[0],0,atol=1e-12)
    def test_rotation(self):
        local,o,A,n=geometry(self.poly,55,.24)
        np.testing.assert_allclose(A.T@A,np.eye(2),atol=1e-12)
        np.testing.assert_allclose(A.T@n,0,atol=1e-12)
    def test_screen_symmetry(self):
        local,o,A,n=geometry(self.poly,0,0)
        b=ScreenBasis(local,2)
        B=coupling(b,o,A,n,[[.5,.5,.7],[.5,.5,-.7]],2.,14)
        np.testing.assert_allclose(B[:,0],-B[:,1],atol=1e-12)
        near,Z,q=solve_screen(local,o,A,n,np.array([[.5,.5,.7],[.5,.5,-.7]]),np.array([[.5,.5,1.]]),2.,3,10,18)
        self.assertTrue(np.isfinite(near).all())
        self.assertLess(q['powerRelative'],.01,q)
        self.assertLess(q['reciprocity'],.001,q)
if __name__=='__main__':unittest.main()

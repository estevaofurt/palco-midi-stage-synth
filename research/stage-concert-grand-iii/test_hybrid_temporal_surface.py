import unittest
import numpy as np
from hybrid_temporal_surface import surface_basis,residuals,response_states,harmonic_discrete
class SurfaceTest(unittest.TestCase):
    def test_known_gram(self):
        H=np.diag([4.,1.,0.]);ev,W=surface_basis(H)
        X=np.ones((2,3,1),complex)
        self.assertAlmostEqual(residuals(H,ev,W,X,1)['maximum'],np.sqrt(.2))
        self.assertLess(residuals(H,ev,W,X,2)['maximum'],1e-12)
    def test_invalid(self):
        with self.assertRaises(ValueError):surface_basis(np.diag([1.,-1.]))
    def test_warp(self):
        k=(2*np.pi*np.array([30.,100.]))**2;D=np.eye(2)*10;P=np.eye(2)
        self.assertLess(harmonic_discrete(k,D,P,[30.,80.,100.],48000)['maximum'],.005)
if __name__=='__main__':unittest.main()

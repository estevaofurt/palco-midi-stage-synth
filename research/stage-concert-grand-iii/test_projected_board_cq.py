import unittest
import numpy as np
from projected_board_cq import simulate,harmonic
class BoardCQTest(unittest.TestCase):
    def test_memory_and_energy(self):
        k=np.array([1e5,2e5]);D=np.eye(2);U=np.array([[1.],[0.]])
        # Passive FIR: R*(1-z), exact nonnegative accumulated work.
        W=np.array([[[.5]],[[-.5]]])
        F=np.zeros((512,2));F[:100,0]=1.
        r=simulate(k,D,U,W,48000,F)
        self.assertTrue(r['gate'],r)
        self.assertGreater(r['acousticPortWorkJ'],0.)
        d=simulate(k,D,U,np.zeros((1,1,1)),48000,F)
        self.assertTrue(d['gate'],d);self.assertEqual(d['acousticPortWorkJ'],0.)
    def test_harmonic(self):
        k=np.array([1e5,2e5]);D=np.eye(2);B=np.eye(2);Z=np.zeros((2,2))
        y,v=harmonic(k,D,B,Z,110.)
        s=2j*np.pi*110
        np.testing.assert_allclose(y,np.diag(s/(k+s*s+s)))
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from mixed_acoustic_midpoint import proof,fixture_weights,Mixed
class MixedTest(unittest.TestCase):
    def test_independent_reference(self):
        M=np.array([[2.,.2],[.2,1.]])
        K=np.array([[1000.,10.],[10.,400.]])
        D=.1*M+.0001*K;P=np.eye(2);A=np.array([[1.,.2],[.4,1.]])
        for r in (48000,96000):
            result=proof(M,K,D,P,A,r,256)
            self.assertTrue(result['gate'],result)
    def test_silence(self):
        C,cfg=fixture_weights(2)
        a=Mixed(np.eye(2),100*np.eye(2),np.eye(2),np.eye(2),np.eye(2),C,cfg,48000)
        o,w,l=a.step(np.zeros(2))
        self.assertEqual(a.energy(),0.);self.assertEqual(w,0.)
        self.assertFalse(np.any(o));self.assertFalse(np.any(l))
if __name__=='__main__':unittest.main()

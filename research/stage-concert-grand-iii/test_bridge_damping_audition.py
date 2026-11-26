import unittest
import numpy as np
from bridge_damping_audition import candidate_damping,late_ratio,RATE
class BridgeAuditionTest(unittest.TestCase):
    def test_damping(self):
        G=np.stack([np.eye(80),2*np.eye(80),4*np.eye(80)])
        np.testing.assert_array_equal(candidate_damping(G,.5),5*np.eye(80))
        with self.assertRaises(ValueError):candidate_damping(G,-1.)
    def test_ratio(self):
        t=np.arange(5*RATE)/RATE;y=np.sin(2*np.pi*261.63*t)[:,None]*np.array([[1.,.5]])
        np.testing.assert_allclose(late_ratio(2*y,y),np.full((5,2),2.))
if __name__=='__main__':unittest.main()

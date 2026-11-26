import unittest
import numpy as np
from acoustic_cq_coupling import hist,g_energy,numerical_loss,simulate
class CouplingTest(unittest.TestCase):
    def test_bdf2_identity(self):
        a,b,c=np.array([[.4,1.],[.2,.3],[-.1,.4]])
        M=np.array([[2.,.1],[.1,1.]])
        lhs=float(a@M@(1.5*a-2*b+.5*c))
        rhs=g_energy(a,b,M)-g_energy(b,c,M)+numerical_loss(a,b,c,M)
        self.assertAlmostEqual(lhs,rhs,places=13)
    def test_independent_states(self):
        r=simulate(48000,512,128)
        self.assertTrue(r['screeningGate'],r)
if __name__=='__main__':unittest.main()

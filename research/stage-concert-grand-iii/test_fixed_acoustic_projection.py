import unittest
import numpy as np
from fixed_acoustic_projection import freeze_projection,eligible,TRAIN,CHECK,NOVEL
class FixedRankTest(unittest.TestCase):
    def test_projection(self):
        Z=np.stack([np.diag(np.arange(1.,7.))+1j*np.diag(np.arange(6.,0.,-1.))])
        U=freeze_projection(Z,4)
        np.testing.assert_allclose(U.T@U,np.eye(4),atol=1e-12)
    def test_matrix_gate(self):
        self.assertTrue(eligible(dict(powerGate=True,maximumMatrix=.009,maximumResponse=.04)))
        self.assertFalse(eligible(dict(powerGate=True,maximumMatrix=.011,maximumResponse=.01)))
        self.assertFalse(eligible(dict(powerGate=True,maximumMatrix=.001,maximumResponse=.051)))
    def test_reserved(self):
        self.assertFalse(set(TRAIN)&set(CHECK));self.assertFalse(set(TRAIN)&set(NOVEL));self.assertFalse(set(CHECK)&set(NOVEL))
if __name__=='__main__':unittest.main()

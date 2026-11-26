import unittest
import numpy as np
from acoustic_port_rank import basis,projected,summarize
class PortRankTest(unittest.TestCase):
    def test_nested_port_basis(self):
        B=np.eye(6)[:,:2];X=np.arange(18.).reshape(6,3)+1j*np.eye(6)[:,:3]
        U=basis(B,[X])
        np.testing.assert_allclose(U.T@U,np.eye(6),atol=1e-12)
        np.testing.assert_allclose(U[:,:2]@U[:,:2].T@B,B,atol=1e-12)
        Z=np.diag(np.arange(1.,7.))+1j*np.eye(6)
        np.testing.assert_allclose(projected(Z,U),Z,atol=1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(projected(Z,U[:,:3]).real).min(),-1e-12)
    def test_rank_rejection(self):
        with self.assertRaises(ValueError):basis(np.ones((4,2)),[np.eye(4)])
    def test_summary(self):
        r=summarize([dict(maximumResponse=.02,matrix=dict(impedance=.1),powerGate=True)])
        self.assertEqual(r['maximumResponse'],.02);self.assertEqual(r['maximumMatrix'],.1)
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from snapshot_reduction import snapshot_bases
class SnapshotTest(unittest.TestCase):
    def test_real_subspace(self):
        rng=np.random.default_rng(5);Q,_=np.linalg.qr(rng.normal(size=(9,2)))
        F=np.stack([Q@(rng.normal(size=(2,4))+1j*rng.normal(size=(2,4))) for _ in range(5)])
        B,_=snapshot_bases(F,[9],[2.],4);U=B[0]
        self.assertEqual(U.shape,(9,2))
        np.testing.assert_allclose(U.T@U,np.eye(2),atol=1e-12)
        np.testing.assert_allclose(U@U.T,Q@Q.T,atol=1e-12)
    def test_panel_separation(self):
        F=np.ones((3,7,4),complex);F[:,3:]*=1j
        B,_=snapshot_bases(F,[3,4],[1.,2.],2)
        self.assertEqual([b.shape for b in B],[(3,1),(4,1)])
    def test_bad_area(self):
        with self.assertRaises(ValueError):snapshot_bases(np.ones((2,3,4)),[3],[0.],2)
if __name__=='__main__':unittest.main()

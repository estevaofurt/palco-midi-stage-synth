import unittest
import numpy as np
from acoustic_rank_fit import projected_target,objective
class RankFitTest(unittest.TestCase):
    def test_projection(self):
        Z=np.array([[[2.+1j,.1],[.1,1.+2j]]])
        U=np.eye(2)
        np.testing.assert_allclose(projected_target(Z,U,2),Z)
        np.testing.assert_allclose(projected_target(Z,U,1),[[[2.+1j,0],[0,0]]])
        with self.assertRaises(ValueError):projected_target(Z,U,0)
    def test_objective(self):
        self.assertEqual(objective(dict(matrixMaximum=.02,responseMaximum=.1)),.1)
if __name__=='__main__':unittest.main()

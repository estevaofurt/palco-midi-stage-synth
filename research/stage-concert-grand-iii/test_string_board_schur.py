import unittest
import numpy as np
from string_board_schur import StringBoard,fixture,probe
from contiguous_midpoint import stress_model
class StringBoardTest(unittest.TestCase):
    def test_dense_equivalence(self):
        self.assertTrue(probe(4,3,8000,.04,12)['gate'])
    def test_zero_coupling(self):
        b=stress_model(8,5,8000)
        a=StringBoard(b,[1.],[100.],[0.],np.ones((1,4)),[0.],[0.])
        W=0.
        for _ in range(100):
            w=a.step(np.zeros(8),np.ones(1));W+=w[0]
            self.assertEqual(w[2],0.)
        np.testing.assert_array_equal(b.q,np.zeros(8))
        self.assertAlmostEqual(W,a.energy(),places=12)
    def test_negative(self):
        with self.assertRaises(ValueError):StringBoard(stress_model(8,5,8000),[1.],[100.],[0.],np.ones((1,4)),[-1.],[0.])
if __name__=='__main__':unittest.main()

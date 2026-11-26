import unittest
import numpy as np
from same_geometry_modal_comparison import maps
from scipy.linalg import block_diag
class ModalTest(unittest.TestCase):
    def test_nested(self):
        counts=[61,63,63,63,63,61,55]
        idx=np.concatenate([np.arange(j,j+55) for j in np.r_[0,np.cumsum(counts)[:-1]]])
        m=maps(counts,idx)
        a,b=(block_diag(*m[n]) for n in (355,385))
        self.assertEqual(a.shape,(429,355));self.assertEqual(b.shape,(429,385))
        np.testing.assert_array_equal(a.T@a,np.eye(355))
        np.testing.assert_array_equal(b@(b.T@a),a)
        with self.assertRaises(ValueError):maps(counts,idx[::-1])
if __name__=='__main__':unittest.main()

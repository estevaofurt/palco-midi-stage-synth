import unittest
import numpy as np
from bem_third_strip_replay import mark_scores,validate_source
class ThirdStripTest(unittest.TestCase):
    def test_band_marking(self):
        classes=np.array([['crease','mesh-edge','crease-port-transition']])
        a=np.arange(9.).reshape(1,3,3)
        s,m=mark_scores(dict(sectorBandIndicator=a),classes)
        np.testing.assert_array_equal(s,[[0,3,6]])
        np.testing.assert_array_equal(m,[[True,False,True]])
        with self.assertRaises(ValueError):mark_scores(dict(sectorBandIndicator=-a),classes)
    def test_missing_evidence(self):
        with self.assertRaises(ValueError):validate_source({}, {},30,'a'*64)
if __name__=='__main__':unittest.main()

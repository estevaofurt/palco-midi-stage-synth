import unittest
import numpy as np
from bem_strip_band_replay import compare_bands,validate_archive
from bem_edge_localization import summarize
class ReplayTest(unittest.TestCase):
    def test_closure_and_comparison(self):
        c=np.array([['crease','mesh-edge','mesh-edge']])
        E=np.ones((1,3,3,2));T=np.ones_like(E);A=np.ones(E.shape[:3])
        a=summarize(c,E,T,A)
        np.testing.assert_allclose(np.asarray(a['sectorBandIndicator']).sum(2),a['sectorIndicator'])
        self.assertTrue(compare_bands(a,a)['gate'])
        E[0,0,0]*=4;b=summarize(c,E,T,A)
        self.assertFalse(compare_bands(a,b)['gate'])
    def test_incomplete_archive(self):
        with self.assertRaises(ValueError):validate_archive({}, {},30,'a'*64)
if __name__=='__main__':unittest.main()

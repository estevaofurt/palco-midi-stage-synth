import unittest
import numpy as np
from structural_region_decay import project_regions,factors
class RegionTest(unittest.TestCase):
    def test_projection(self):
        D=np.diag([1.,2.,3.,4.]);V=np.array([[1.,0.],[.2,.4],[.1,.7],[.3,.2]])
        G,a=project_regions(D,V,[2,1,1])
        np.testing.assert_allclose(G.sum(axis=0),V.T@D@V,rtol=1e-14,atol=1e-14)
        self.assertLess(a['reconstructionRelative'],1e-12)
        D[0,2]=D[2,0]=.1
        with self.assertRaises(ValueError):project_regions(D,V,[2,1,1])
    def test_variants(self):
        self.assertEqual(len(factors()),7)
        self.assertEqual(factors()[0],(1.,1.,1.))
if __name__=='__main__':unittest.main()

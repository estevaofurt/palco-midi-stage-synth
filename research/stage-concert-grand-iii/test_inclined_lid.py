import unittest
import numpy as np
from inclined_lid import build,matched_fixture
from closed_cavity import response
class LidTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.,2.],[0.,2.]])
        self.field=lambda xy:np.c_[np.ones(len(xy)),xy[:,0]]
    def test_closed_limit(self):
        m,C,q=build(self.poly,4,2,.24,0,self.field)
        self.assertEqual(C.shape[1],0);self.assertAlmostEqual(m['volume'],.48)
    def test_three_sides_and_volume(self):
        for a in (15,30,55):
            m,C,q=build(self.poly,4,2,.24,a,self.field)
            self.assertEqual(q['ports'],3)
            self.assertAlmostEqual(q['wedgeVolumeM3'],np.sin(np.deg2rad(a)))
            np.testing.assert_allclose(C.sum(0),1,atol=1e-12)
            d=2*np.sin(np.deg2rad(a)/2)
            self.assertAlmostEqual(q['areaM2'],2*d+np.sin(np.deg2rad(a)))
            self.assertTrue(q['gate'])
    def test_reciprocal_fixture(self):
        m,C,q=build(self.poly,5,3,.24,30,self.field)
        for f in (30,80,150):
            Z,P,U,rep=matched_fixture(m,C,q,2j*np.pi*f,[[.3,.6,.12],[.7,1.4,.18]])
            self.assertTrue(rep['gate']);self.assertEqual(U.shape,(3,2))
    def test_nonrectangular(self):
        poly=np.array([[0.,0.],[1.,0.],[1.2,.7],[.7,1.5],[0.,1.]])
        m,C,q=build(poly,6,3,.24,55,self.field)
        self.assertEqual(q['ports'],4);self.assertGreater(q['areaM2'],0)
if __name__=='__main__':unittest.main()

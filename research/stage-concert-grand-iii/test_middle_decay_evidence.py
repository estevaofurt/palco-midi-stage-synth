import unittest
from middle_decay_evidence import compare
class MiddleDecayTest(unittest.TestCase):
    def test_ratio(self):
        r=compare([1.]*40,[.5]*40,1.)
        self.assertAlmostEqual(r['intervals'][0]['wetToDryPowerRatio'],.25)
        self.assertAlmostEqual(r['intervals'][0]['rmsDifferenceDb'],-6.020599913279624)
    def test_gap(self):
        x=[0.]*40;x[0]=1.;x[7]=.2;x[-1]=.2
        r=compare(x,x,1.)['occupancy'][0]['wet']
        self.assertEqual(r['windowsAbove'],3)
        self.assertEqual(r['internalBelowWindows'],37)
        self.assertTrue(r['rightCensored'])
    def test_invalid(self):
        with self.assertRaises(ValueError):compare([1.]*39,[1.]*40,1.)
if __name__=='__main__':unittest.main()

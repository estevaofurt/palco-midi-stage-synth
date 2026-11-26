import unittest
from hybrid_midpoint_cq import simulate
class HybridTest(unittest.TestCase):
    def test_coupling(self):
        for rate in (48000,96000):
            r=simulate(rate,512,256)
            self.assertTrue(r['screeningGate'],r)
            self.assertGreaterEqual(r['acousticNumericalDissipationJ'],0.)
            self.assertGreater(r['acousticPhysicalDissipationJ'],0.)
            self.assertFalse(r['mechanicalNumericalDissipationIncluded'])
if __name__=='__main__':unittest.main()

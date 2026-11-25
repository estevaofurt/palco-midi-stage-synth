import unittest,json
from pathlib import Path
from scale_hypothesis import build
from hammer_impact import impact,compare
ROOT=Path(__file__).parent
class ImpactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=json.loads((ROOT/'physical_sources.json').read_text());cls.c=json.loads((ROOT/'felt_hypothesis.json').read_text())
        cls.r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
    def test_rigid(self):
        r=impact(self.r,self.s,self.c,96000,1.,'rigid')
        self.assertEqual(r['targetJ'],0.);self.assertLess(r['reboundMps'],1.);self.assertGreater(r['lossJ'],0.)
    def test_elastic(self):
        r=impact(self.r,self.s,self.c,96000,1.,'elastic')
        self.assertGreater(r['targetJ'],0.);self.assertLess(r['maxBalanceJ'],1e-10)
        self.assertAlmostEqual(r['perImpulseNs'][0],r['perImpulseNs'][2],places=12)
    def test_stagger(self):
        r=impact(self.r,self.s,self.c,96000,1.,'elastic',stagger=True)
        self.assertGreater(max(r['perImpulseNs'])-min(r['perImpulseNs']),1e-8)
    def test_convergence(self):
        a=impact(self.r,self.s,self.c,96000,1.,'elastic');b=impact(self.r,self.s,self.c,192000,1.,'elastic')
        self.assertTrue(compare(a,b)['gate'])
if __name__=='__main__':unittest.main()

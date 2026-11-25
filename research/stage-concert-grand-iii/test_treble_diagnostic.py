import unittest,json
from pathlib import Path
from felt_law import params,force
from treble_diagnostic import alternative,ANCHORS,DREF
from modal_target import basis
from modal_impact import run
from scale_hypothesis import build
ROOT=Path(__file__).parent
class TrebleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=json.loads((ROOT/'physical_sources.json').read_text());cls.c=json.loads((ROOT/'felt_hypothesis.json').read_text())
    def test_anchors(self):
        for k,K,p in ANCHORS:
            a=alternative(k,self.s);m,f=params(k,3,a,self.c)
            self.assertAlmostEqual(3*force(DREF,0.,f)/(K*DREF**p),1.,places=12)
    def test_no_extrapolate(self):
        with self.assertRaises(ValueError):alternative(108,self.s)
    def test_spectrum(self):
        r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
        w,P=basis(r,128,12000,.005)
        q=run(r,self.s,self.c,w,P,96000,1.,trace=True)
        self.assertLess(q['forceSpectrumResidualJ'],1e-12)
if __name__=='__main__':unittest.main()

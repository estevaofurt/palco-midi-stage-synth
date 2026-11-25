import unittest,json
from pathlib import Path
import numpy as np
from modal_target import basis,Target
from scale_hypothesis import build
ROOT=Path(__file__).parent
class ModalTest(unittest.TestCase):
    def test_uniform(self):
        r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
        w2,P=basis(r,128,12000,.005)
        self.assertAlmostEqual(np.sqrt(w2[0])/(2*np.pi),r['nominalHz'],places=7)
        self.assertGreater(len(P),1)
    def test_work(self):
        t=Target(np.array([100.,1000.,1e7]),np.array([1.,-.5,2.]),96000)
        for F in np.sin(np.arange(300)*.07):
            old=t.energy();free=t.free();work=t.step(float(F))
            self.assertAlmostEqual(t.position(),free+t.H*F,places=13)
            self.assertAlmostEqual(t.energy()-old,work,places=12)
    def test_finite_width(self):
        r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][87]
        with self.assertRaises(ValueError):basis(r,128,12000,.02)
if __name__=='__main__':unittest.main()

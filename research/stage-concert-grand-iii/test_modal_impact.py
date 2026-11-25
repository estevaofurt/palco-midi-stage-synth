import unittest,json
from pathlib import Path
from modal_target import basis
from modal_impact import run,compare
from scale_hypothesis import build
ROOT=Path(__file__).parent
class ModalImpactTest(unittest.TestCase):
    def test_C4(self):
        r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
        s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text())
        w,P=basis(r,128,12000,.005)
        a=run(r,s,c,w,P,96000,1.);b=run(r,s,c,w,P,192000,1.)
        self.assertGreater(b['targetJ'],0);self.assertAlmostEqual(sum(b['modalEnergyJ']),b['targetJ'],places=12)
        self.assertTrue(compare(a,b)['gate'])
    def test_stagger(self):
        r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
        s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text())
        w,P=basis(r,128,12000,.005)
        a=run(r,s,c,w,P,96000,1.,True)
        self.assertGreater(max(a['perImpulseNs'])-min(a['perImpulseNs']),1e-8)
if __name__=='__main__':unittest.main()

import unittest,json
from pathlib import Path
import numpy as np
from loaded_target import LoadedTarget
from moving_termination import basis
from termination_diagnostic import LOAD
from modal_impact import run
from scale_hypothesis import build
ROOT=Path(__file__).parent
class LoadedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
        cls.w,cls.P=basis(cls.r,128,24000,LOAD['massKg'],LOAD['stiffnessNm'])
    def test_affine(self):
        t=LoadedTarget(self.w,self.P,192000,LOAD)
        for F in np.sin(np.arange(400)*.04):
            before=t.energy();l=t.loss;free=t.free();work=t.step(float(F))
            self.assertAlmostEqual(t.position(),free+t.H*F,places=13)
            self.assertLess(abs(t.energy()-before-work+t.loss-l),1e-12)
            self.assertLessEqual(t.load_energy(),t.energy()+1e-12)
        self.assertGreater(t.loss,0.)
    def test_impact(self):
        s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text())
        q=run(self.r,s,c,self.w,self.P,192000,1.,target_factory=lambda w,P,sr:LoadedTarget(w,P,sr,LOAD))
        self.assertGreater(q['boundaryLossJ'],0)
        self.assertAlmostEqual(q['netTargetWorkJ'],q['stringStoredJ']+q['loadStoredJ']+q['boundaryLossJ'],places=11)
        self.assertLess(q['maxBalanceJ'],1e-10)
    def test_reject_spectrum(self):
        s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text())
        with self.assertRaises(ValueError):run(self.r,s,c,self.w,self.P,192000,1.,trace=True,target_factory=lambda w,P,sr:LoadedTarget(w,P,sr,LOAD))
if __name__=='__main__':unittest.main()

import unittest,math,json
from pathlib import Path
import numpy as np
from flexible_hammer import Hammer
from modal_impact import run
from modal_target import basis
from scale_hypothesis import build
from shaft_diagnostic import SHAFT
ROOT=Path(__file__).parent
class HammerTest(unittest.TestCase):
    def test_rigid(self):
        t=Hammer(.008,96000,1.);h=t.h;self.assertAlmostEqual(t.energy(),.004)
        t.step(-10.);self.assertAlmostEqual(t.position(),h-10*h*h/(2*.008),places=15);self.assertEqual(t.flex_energy(),0.)
    def test_flex_work(self):
        t=Hammer(.008,96000,1.,SHAFT)
        self.assertAlmostEqual(t.energy(),.004);self.assertAlmostEqual(t.velocity(),1.)
        impulse=0.
        for F in -10*np.sin(np.arange(200)*.07)**2:
            old=t.energy();free=t.free();work=t.step(float(F));impulse+=F*t.h
            self.assertAlmostEqual(t.position(),free+t.H*F,places=14)
            self.assertAlmostEqual(t.energy()-old,work,places=13)
        self.assertGreater(t.flex_energy(),0.);self.assertAlmostEqual(.008*(t.v-1.),impulse,places=13)
    def test_coupled(self):
        r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
        s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text())
        w,P=basis(r,128,12000,.005)
        x=run(r,s,c,w,P,96000,1.,trace=True,shaft=SHAFT)
        self.assertGreater(x['shaftEnergyJ'],0.);self.assertLess(x['maxBalanceJ'],1e-10)
    def test_domain(self):
        with self.assertRaises(ValueError):Hammer(.008,96000,1.,dict(headMassFraction=1.,relativeModeHz=260.))
if __name__=='__main__':unittest.main()

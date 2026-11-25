import unittest,json
from pathlib import Path
from action_launch import launch,state_at
ROOT=Path(__file__).parent
class ActionTest(unittest.TestCase):
    def setUp(self):
        self.s=json.loads((ROOT/'physical_sources.json').read_text());self.c=json.loads((ROOT/'action_hypothesis.json').read_text())
    def test_note_off(self):self.assertIsNone(launch(60,0,self.s,self.c))
    def test_domain(self):
        for k,v in ((20,1),(109,1),(60,-1),(60,128),(60,1.2)):
            with self.assertRaises(ValueError):launch(k,v,self.s,self.c)
    def test_monotonic(self):
        q=[launch(60,v,self.s,self.c) for v in range(1,128)]
        self.assertTrue(all(x['impactEnergyJ']<y['impactEnergyJ'] for x,y in zip(q,q[1:])))
        self.assertAlmostEqual(q[0]['impactSpeedMps'],.3);self.assertAlmostEqual(q[-1]['impactSpeedMps'],5.)
    def test_escape(self):
        q=launch(60,76,self.s,self.c);z=state_at(q,q['drivenDurationS'],self.c)
        self.assertEqual(z['stage'],'free');self.assertEqual(z['driveForceN'],0.)
        self.assertAlmostEqual(z['travelM'],.044,places=12)
        z=state_at(q,q['fullTravelS'],self.c);self.assertAlmostEqual(z['travelM'],.046,places=12)
        self.assertAlmostEqual(z['speedMps'],q['impactSpeedMps'],places=12)
    def test_energy(self):
        q=launch(60,127,self.s,self.c);self.assertAlmostEqual(q['actionWorkJ'],q['impactEnergyJ']+q['gravityTotalJ'],places=12)
        self.assertFalse(q['scheduledPreRoll'])
if __name__=='__main__':unittest.main()

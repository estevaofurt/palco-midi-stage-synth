import json,math,unittest
from pathlib import Path
from scale_hypothesis import build,winding,wrap_mass,interp
class ScaleTests(unittest.TestCase):
    def setUp(self):self.c=json.loads(Path(__file__).with_name('scale_hypothesis.json').read_text())
    def test_coverage(self):
        r=build(self.c);self.assertEqual([x['key'] for x in r['rows']],list(range(21,109)));self.assertEqual(r['summary']['strings'],226);self.assertEqual(r['summary']['wrappedKeys'],29);self.assertFalse(r['summary']['scaleReady'])
    def test_balance(self):
        for x in build(self.c)['rows']:
            self.assertAlmostEqual(x['analyticalHz'],x['nominalHz'],places=8)
            self.assertAlmostEqual(x['tensionPerStringN'],4*x['lengthM']**2*x['nominalHz']**2*x['linearDensityKgM']-math.pi**2*x['bendingNm2']/x['lengthM']**2,places=8)
    def test_transitions(self):
        r=build(self.c);self.assertEqual([x['keys'] for x in r['edges'] if x['transition']],[[29,30],[46,47],[49,50]])
        self.assertTrue(all(x['review'] for x in r['edges'] if x['transition']))
    def test_winding(self):
        for n in (1,2):
            w=winding(.001,.02,n,8960,.9);self.assertAlmostEqual(.9*wrap_mass(.001,w,n,8960),.02,places=12)
    def test_invalid_winding(self):
        with self.assertRaises(ValueError):winding(.001,-1,1,8960,.9)
    def test_no_extrapolation(self):
        with self.assertRaises(ValueError):interp(20,[[21,1],[25,2]])
    def test_reject_stress(self):
        self.c['screen']['maxCoreStressPa']=1
        with self.assertRaises(ValueError):build(self.c)
if __name__=='__main__':unittest.main()

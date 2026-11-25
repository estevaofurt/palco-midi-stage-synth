import copy,json,math,unittest
from pathlib import Path
from physical_inventory import build,derive
class InventoryTests(unittest.TestCase):
    def setUp(self):self.s=json.loads(Path(__file__).with_name('physical_sources.json').read_text())
    def test_scope(self):
        a=build(self.s);self.assertEqual([r['key'] for r in a['rows']],list(range(21,109)))
        self.assertFalse(a['summary']['scaleReady'])
        self.assertEqual(a['summary']['stringAnchorPriors'],6)
        self.assertTrue(all(v is None for r in a['rows'] for v in r['targetPhysical'].values()))
    def test_hammer(self):
        rows=build(self.s)['rows'];self.assertTrue(all(a['hammerPrior']['massKg']>b['hammerPrior']['massKg'] for a,b in zip(rows,rows[1:])))
        self.assertTrue(all(r['hammerPrior']['forceAt1mmN']>0 for r in rows))
    def test_anchor(self):
        a=next(r for r in build(self.s)['rows'] if r['key']==60)['stringPrior']['derived']
        self.assertAlmostEqual(a['strikeFraction'],.079/.657)
        self.assertTrue(0<a['inharmonicity']<.01)
        self.assertLess(abs(a['frequencyGapCents']),15)
    def test_bad_anchor(self):
        a=copy.deepcopy(self.s['anchors'][0]);a['L']=0
        with self.assertRaises(ValueError):derive(a,202e9)
    def test_duplicate(self):
        self.s['anchors'].append(self.s['anchors'][0])
        with self.assertRaises(ValueError):build(self.s)
if __name__=='__main__':unittest.main()

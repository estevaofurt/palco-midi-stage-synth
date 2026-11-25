import json,unittest
from pathlib import Path
from scale_geometry import candidate
from scale_hypothesis import build
from wound_modes import solve
ROOT=Path(__file__).parent
class GeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads((ROOT/'scale_hypothesis.json').read_text());rows=[]
        for r in build(cls.c)['rows'][:29]:
            x=solve(r,128,cls.c['wrappedFraction'],cls.c['screen']);T=x['T'];mu=r['linearDensityKgM']
            rows.append(dict(key=r['key'],oldTensionN=r['tensionPerStringN'],retunedTensionN=T,coreStressPa=T/(3.141592653589793*r['coreDiameterM']**2/4),modalFrequenciesHz=x['corrected'].tolist(),newAverageGroupZ=r['count']*(T*mu)**.5,bareImpedanceNsM=(T*r['coreMassPerM'])**.5,wrappedImpedanceNsM=(T*x['localMu'])**.5,windingIntervalM=[x['start'],x['end']]))
        cls.w=dict(summary=dict(gate=True),rows=rows);cls.r=candidate(cls.c,cls.w)
    def test_ports(self):
        self.assertEqual(len(self.r['wires']),226)
        for w in self.r['wires']:
            p={p['role']:p for p in w['ports']}
            self.assertEqual(p['front']['localS_m'],0)
            self.assertEqual(p['bridge']['localS_m'],w['lengthM'])
            self.assertTrue(0<p['hammer']['localS_m']<w['lengthM'])
            self.assertIsNone(p['damper']['localS_m'])
            self.assertTrue(all(v['worldXYZ_m'] is None for v in p.values()))
    def test_transition(self):
        self.assertAlmostEqual(self.r['edges'][28]['newAverageDeltaDb'],2.5,places=8)
        self.assertTrue(self.r['edges'][28]['endpointReview'])
        self.assertFalse(self.r['summary']['scaleReady'])
    def test_no_alias(self):
        p=[p['id'] for w in self.r['wires'] for p in w['ports']]
        self.assertEqual(len(p),len(set(p)))
    def test_no_fake_geometry(self):
        self.assertFalse(self.r['summary']['geometryReady'])
        self.assertTrue(all(w['globalFrame'] is None and w['rearNonSpeakingLengthM'] is None for w in self.r['wires']))
if __name__=='__main__':unittest.main()

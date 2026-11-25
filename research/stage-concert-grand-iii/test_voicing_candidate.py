import unittest,json,math
from pathlib import Path
from voicing_candidate import candidate,inventory,REF,K7,P7
from physical_inventory import hammer
from felt_law import params,force
from scale_hypothesis import build
ROOT=Path(__file__).parent
class VoicingTest(unittest.TestCase):
    def setUp(self):
        self.s=json.loads((ROOT/'physical_sources.json').read_text());self.c=json.loads((ROOT/'felt_hypothesis.json').read_text())
    def test_original(self):
        for k in range(21,73):self.assertEqual(candidate(k,self.s),self.s)
    def test_anchor(self):
        for k in (96,108):
            h,f=params(k,3,candidate(k,self.s),self.c)
            self.assertAlmostEqual(3*force(REF,0.,f),K7*REF**P7,places=10)
            self.assertAlmostEqual(f.p,P7)
    def test_inventory(self):
        r=inventory(self.s,self.c,build(json.loads((ROOT/'scale_hypothesis.json').read_text())))
        self.assertEqual(r['summary']['keys'],88);self.assertFalse(r['summary']['selected'])
    def test_domain(self):
        with self.assertRaises(ValueError):candidate(109,self.s)
if __name__=='__main__':unittest.main()

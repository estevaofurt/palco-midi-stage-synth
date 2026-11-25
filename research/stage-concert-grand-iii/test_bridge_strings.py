import unittest,json,os
from pathlib import Path
import numpy as np
from bridge_strings import centerline,assemble,Coupled
from string_ports import element
ROOT=Path(__file__).parent
class CoupledTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sc=json.loads(Path(os.environ['G3_SCALE_REPORT']).read_text());cls.rows={r['key']:r for r in sc['rows']}
        cls.cfg=json.loads((ROOT/'bridge_hypothesis.json').read_text())
        cls.center=centerline([dict(key=k,wireId=f'{k}-{i}',xyzM=[(k-60)*.1+i*.002,.5,0]) for k in (60,61,62) for i in (-1,0,1)])
    def test_centerline(self):
        self.assertEqual(self.center['keys'],[60,61,62]);self.assertAlmostEqual(self.center['lengthM'],.2)
        self.assertAlmostEqual(self.center['maxOffsetM'],.002)
    def test_mass_once(self):
        M,K,P,parts,b=assemble(self.center,self.rows,[60,61],2,32,self.cfg,'treble')
        nb=len(b['M']);expected=b['M'].copy()
        for key in (60,61):
            A,_,_=element(self.rows[key],32);i=b['attachmentDofs'][self.center['keys'].index(key)];expected[i,i]+=A[1,1]
        np.testing.assert_allclose(M[:nb,:nb],expected,atol=1e-14)
        self.assertGreater(np.linalg.eigvalsh(M)[0],0.)
    def test_cross_transfer(self):
        args=(self.center,self.rows,[60,61],2,64,24000,192000,self.cfg,'treble')
        a=Coupled(*args);b=Coupled(*args);work=0.;peak=0.
        for f in np.sin(np.arange(2000)*.04):
            work+=a.step([f,0,0,0]);b.step([0,f,0,0])
            self.assertLess(abs(a.energy()+a.loss-work),1e-12)
            self.assertAlmostEqual(a.position()[1],b.position()[0],places=13)
            peak=max(peak,abs(a.position()[1]))
        self.assertGreater(peak,1e-12);self.assertGreater(a.partition()['61'],0.)
if __name__=='__main__':unittest.main()

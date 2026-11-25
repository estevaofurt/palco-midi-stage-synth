import unittest,json
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky
from board_contour import hull
from spline_plate import assemble
from structural_assembly import assemble as coupled,mobility
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
class StructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=hull([[0,0],[1,0],[1,1.2],[0,1.2]])
        cls.ic=read('board_interface_hypothesis.json');cls.rc=read('rim_structure_hypothesis.json');cls.bc=read('bridge_hypothesis.json')
        cls.m=assemble(cls.p,[],cls.ic['plate'],read('ribbed_plate_hypothesis.json')['rib'],4,12,False)
        cls.centers={s:dict(xyz=np.array([[.2,.3+j*.4,0],[.5,.4+j*.4,0],[.8,.5+j*.4,0]]),keys=[1,2,3]) for j,s in enumerate(('bass','treble'))}
    def fixture(self,connected=True):return coupled(self.m,self.centers,self.bc,self.ic,self.rc,2,2,8,connected)
    def test_work(self):
        a=self.fixture();x=np.sin(np.arange(len(a['M'])))*1e-5;v=np.cos(np.arange(len(x)))*1e-3
        work=sum(self.ic['joint']['stiffnessNperM2']*float(w@((R@x)*(R@v))) for R,w in a['maps'])
        self.assertAlmostEqual(float(v@a['Jbridge']@x),work,places=12)
        cholesky(a['M']);cholesky(a['K']+a['Jrim']+a['Jbridge'])
    def test_no_duplicate_mass(self):
        a=self.fixture();b=self.fixture(False)
        np.testing.assert_array_equal(a['M'],b['M'])
        np.testing.assert_array_equal(a['K'],b['K'])
        self.assertAlmostEqual(a['rimMassKg'],4.4*660*.04*.08,places=10)
        self.assertEqual(sum([a['plateDofs'],a['rimDofs'],*a['bridgeDofs']]),len(a['M']))
    def test_cross(self):
        y,_,_=mobility(self.fixture(),[50.,100.,150.]);z,_,_=mobility(self.fixture(False),[50.,100.,150.])
        self.assertGreater(np.max(abs(y[:,0,2])),1e-10)
        self.assertLess(np.max(abs(z[:,0,2])),1e-14)
        self.assertGreater(np.max(abs(y[:,0,4])),1e-10)
if __name__=='__main__':unittest.main()

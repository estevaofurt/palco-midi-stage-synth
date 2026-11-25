import unittest,json
from pathlib import Path
import numpy as np
from shared_unison import assemble,SharedUnison
from moving_termination import basis,Boundary
from termination_diagnostic import LOAD
from scale_hypothesis import build
ROOT=Path(__file__).parent
class UnisonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
    def test_mass_once(self):
        M,K,P,parts=assemble(self.r,32,LOAD,[0,0,0])
        self.assertAlmostEqual(M[0,0],LOAD['massKg']+3*self.r['linearDensityKgM']*self.r['lengthM']/3,places=13)
        self.assertAlmostEqual(K[0,0],LOAD['stiffnessNm']+3*self.r['tensionPerStringN']/self.r['lengthM'])
    def test_single_parity(self):
        r=dict(self.r,count=1);t=SharedUnison(r,64,24000,192000,LOAD,[0])
        w,P=basis(r,64,24000,LOAD['massKg'],LOAD['stiffnessNm']);b=Boundary(w,P,192000,LOAD['dampingNsm'])
        for f in np.sin(np.arange(500)*.04):
            t.step([f,0]);b.step([f,0])
            np.testing.assert_allclose(t.position(),b.position(),atol=1e-12,rtol=1e-8)
    def test_symmetry_and_transfer(self):
        a=SharedUnison(self.r,64,24000,192000,LOAD,[0,0,0]);b=SharedUnison(self.r,64,24000,192000,LOAD,[0,0,0]);work=0.
        for f in np.sin(np.arange(2000)*.04):
            work+=a.step([f,0,0,0]);b.step([0,f,0,0])
            self.assertLess(abs(a.energy()+a.loss-work),1e-12)
            self.assertAlmostEqual(a.position()[1],a.position()[2],places=13)
            self.assertAlmostEqual(a.position()[1],b.position()[0],places=13)
        e,_=a.partition();self.assertGreater(e[1],0.)
    def test_equal_drive(self):
        a=SharedUnison(self.r,64,24000,192000,LOAD,[0,0,0])
        for f in np.sin(np.arange(500)*.04):a.step([f,f,f,0])
        np.testing.assert_allclose(a.position()[:3],a.position()[0],atol=1e-13)
if __name__=='__main__':unittest.main()

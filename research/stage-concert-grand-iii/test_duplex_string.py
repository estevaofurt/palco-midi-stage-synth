import unittest,json
from pathlib import Path
import numpy as np
from scale_hypothesis import build
from duplex_string import Duplex,assemble,Decay
from duplex_diagnostic import LOSS,ZERO
from termination_diagnostic import LOAD
from moving_termination import basis,Boundary
ROOT=Path(__file__).parent
class DuplexTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
    def test_mass_once(self):
        M,K,P,parts=assemble(self.r,32,LOAD,.25)
        self.assertAlmostEqual(M[0,0],LOAD['massKg']+self.r['linearDensityKgM']*self.r['lengthM']*1.25/3,places=13)
    def test_no_duplex_parity(self):
        t=Duplex(self.r,64,24000,192000,LOAD,0.,ZERO)
        w,P=basis(self.r,64,24000,LOAD['massKg'],LOAD['stiffnessNm']);b=Boundary(w,P,192000,LOAD['dampingNsm'])
        for f in np.sin(np.arange(400)*.04):
            t.step([f,0]);b.step([f,0]);np.testing.assert_allclose(t.position(),b.position(),atol=1e-12,rtol=1e-8)
    def test_decay(self):
        d=Decay(np.diag([2.,4.]),.01);v=np.array([1.,2.]);z,L=d.step(v)
        np.testing.assert_allclose(z,v*np.exp(-np.array([2.,4.])*.01));self.assertAlmostEqual(L,.5*(v@v-z@z),places=13)
        with self.assertRaises(ValueError):Decay(np.diag([1.,-1.]),.01)
    def test_partition(self):
        t=Duplex(self.r,64,24000,192000,LOAD,.25,LOSS);work=0.
        for f in np.sin(np.arange(2000)*.04):
            work+=t.step([f,0]);self.assertLess(abs(t.energy()+t.loss-work),1e-12)
        self.assertGreater(t.partition()['duplexJ'],0);self.assertGreater(t.lossMain,0);self.assertGreater(t.lossDuplex,0)
        self.assertAlmostEqual(sum(t.partition().values()),t.energy(),places=12)
if __name__=='__main__':unittest.main()

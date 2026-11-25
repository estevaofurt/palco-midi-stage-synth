import unittest,json
from pathlib import Path
import numpy as np
from scale_hypothesis import build
from vector_unison import VectorUnison
from polarization_diagnostic import ANISO,ISO,ANGLE
from axial_fixture import AxialFixture
ROOT=Path(__file__).parent
class VectorAxialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
    def test_vector_work(self):
        t=VectorUnison(self.r,64,24000,192000,ANISO,ANGLE,[0.,0.,0.]);work=0.;peak=0.
        for f in np.sin(np.arange(1500)*.04):
            F=np.zeros((4,2));F[0,0]=f;work+=t.step(F)
            self.assertLess(abs(t.energy()+t.loss-work),1e-12);peak=max(peak,abs(t.position()[1,1]))
        self.assertGreater(peak,1e-12);e,b=t.partition();self.assertAlmostEqual(sum(e)+b,t.energy(),places=12)
    def test_vector_iso(self):
        t=VectorUnison(self.r,64,24000,192000,ISO,ANGLE,[0.,0.,0.])
        for f in np.sin(np.arange(500)*.04):
            F=np.zeros((4,2));F[0,0]=f;t.step(F)
        self.assertLess(np.max(abs(t.position()[:,1])),1e-12)
    def test_gradient(self):
        t=AxialFixture(self.r,1536000,.0001);q=np.array([1e-4,2e-5,1e-7]);x=np.array([-3e-5,4e-5,-1e-7])
        self.assertAlmostEqual(t.potential(x)-t.potential(q),float(t.gradient(q,x)@(x-q)),places=15)
    def test_axial(self):
        t=AxialFixture(self.r,1536000,.0001);E=t.energy();peak=0.
        for _ in range(1000):
            t.step();peak=max(peak,abs(t.q[2]));self.assertLess(abs(t.energy()-E),1e-12)
        self.assertGreater(peak,0.)
if __name__=='__main__':unittest.main()

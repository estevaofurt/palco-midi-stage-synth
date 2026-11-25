import unittest,json,math
from pathlib import Path
import numpy as np
from scale_hypothesis import build
from polarized_wire import PolarizedWire
ROOT=Path(__file__).parent
ISO=dict(massKg=.005,stiffnessNm=[1e6,1e6],dampingNsm=[5.,5.])
ANISO=dict(massKg=.005,stiffnessNm=[1e6,4e6],dampingNsm=[5.,10.])
class PolarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows'][39]
    def test_isotropic(self):
        t=PolarizedWire(self.r,128,24000,192000,ISO,.43)
        for i in range(400):t.step([[.1*math.sin(i*.03),0],[0,0]])
        self.assertLess(abs(t.position()[0,1]),1e-15)
        self.assertLess(abs(t.position()[1,1]),1e-15)
    def test_aligned(self):
        t=PolarizedWire(self.r,128,24000,192000,ANISO,0.)
        for i in range(400):t.step([[.1*math.sin(i*.03),0],[0,0]])
        self.assertEqual(t.position()[1,1],0.)
    def test_cross_and_energy(self):
        t=PolarizedWire(self.r,128,24000,192000,ANISO,.43);w=0.;peak=0.
        for i in range(1500):
            z=t.step([[.1*math.sin(i*.03),0],[0,0]]);w+=z['work']
            peak=max(peak,abs(t.position()[1,1]))
            self.assertLess(abs(t.energy()+t.loss-w),1e-12)
            self.assertLessEqual(t.load_energy(),t.energy()+1e-12)
        self.assertGreater(peak,1e-12)
    def test_json(self):
        from polarization_diagnostic import compare
        a=dict(trace=np.ones((2,2,2)).tolist(),workJ=np.float64(1),lossJ=np.float64(1),storedJ=np.float64(1))
        q=compare(a,a)
        self.assertIs(type(q['gate']),bool)
        self.assertTrue(json.loads(json.dumps(q,allow_nan=False))['gate'])
    def test_reciprocity(self):
        a=PolarizedWire(self.r,128,24000,192000,ANISO,.43)
        b=PolarizedWire(self.r,128,24000,192000,ANISO,.43)
        for i in range(1000):
            f=.1*math.sin(i*.03);a.step([[f,0],[0,0]]);b.step([[0,0],[0,f]])
            self.assertAlmostEqual(a.position()[1,1],b.position()[0,0],places=14)
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from passive_radiation import Load,spectral
class PassiveTest(unittest.TestCase):
    def test_scalar_transfer(self):
        a=Load([300.],[np.array([[9.]])],15.,np.array([[.02]]));s=10+300j
        self.assertAlmostEqual(a.impedance(s)[0,0],s*.02+9*s/(s*s+30*s+90000))
    def test_power_and_reciprocity(self):
        W=np.array([[[3.,1.],[1.,2.]],[[1.,-.5],[-.5,2.]]]);a=Load([100.,200.],W,10.,np.eye(2)*.01)
        for s in (1j*20,1j*100,1j*200,50+150j,1000+1j):
            Z=a.impedance(s);np.testing.assert_allclose(Z,Z.T,atol=1e-14)
            self.assertGreaterEqual(min(np.linalg.eigvalsh((Z+Z.conj().T)/2)),-1e-12)
    def test_midpoint_budget(self):
        a=Load([100.,400.],np.array([np.eye(2),[[2.,1.],[1.,2.]]]),20.,np.eye(2)*.02)
        W=L=0.;h=1/48000
        for i in range(4800):
            t=(i+1)*h;u=np.array([np.sin(300*t),.2*np.sin(400*t)]) if t<.02 else np.zeros(2)
            _,w,l=a.step(u,h);W+=w;L+=l
            self.assertGreaterEqual(l,0.)
            self.assertLess(abs(W-L-a.storage()),1e-11)
        self.assertGreater(L,0.)
    def test_negative_weight(self):
        with self.assertRaises(ValueError):Load([100.],[[[-1.]]],10.,[[0.]])
if __name__=='__main__':unittest.main()

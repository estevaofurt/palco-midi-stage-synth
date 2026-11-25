import unittest
import numpy as np
from passive_radiation import Load
from vibroacoustic_coupling import Coupled,mobility
class CouplingTest(unittest.TestCase):
    def load(self):return Load([300.,700.],np.array([[[9.,2.],[2.,5.]],[[4.,-1.],[-1.,3.]]]),20.,np.eye(2)*.01)
    def test_budget(self):
        M=np.diag([.02,.03]);K=np.diag([10000.,30000.]);D=np.diag([.2,.3]);A=np.array([[1.,.2],[.1,1.]])
        t=Coupled(M,K,D,A,self.load(),48000);W=0.
        for i in range(2400):
            F=np.array([.1*np.sin(i*.04),0.]) if i<500 else np.zeros(2)
            W+=t.step(F)
            self.assertLess(abs(W-t.energy()-t.lossAir-t.lossStructure),1e-11)
        self.assertGreater(t.lossAir,0.);self.assertGreater(t.lossStructure,0.)
    def test_inertance_once(self):
        M=np.diag([.02,.03]);K=np.diag([10000.,30000.]);D=np.zeros((2,2));A=np.eye(2)
        a=Load([300.],np.zeros((1,2,2)),20.,np.eye(2)*.01)
        t=Coupled(M,K,D,A,a,48000)
        np.testing.assert_allclose(t.Meff,M+a.tail)
        t.v=np.array([.1,.2]);self.assertAlmostEqual(t.energy(),.5*float(t.v@(M+a.tail)@t.v))
    def test_reciprocity_power(self):
        M=np.diag([.02,.03]);K=np.diag([10000.,30000.]);D=np.diag([.2,.3]);A=np.array([[1.,.2],[.1,1.]])
        for f in (80.,250.,1000.):
            Y,m=mobility(M,K,D,A,self.load().impedance(2j*np.pi*f),f)
            self.assertLess(m['powerRelative'],1e-12);self.assertLess(m['reciprocity'],1e-12)
            self.assertGreaterEqual(m['passivityMinRelative'],-1e-12)
            self.assertGreater(abs(Y[0,1]),0.)
if __name__=='__main__':unittest.main()

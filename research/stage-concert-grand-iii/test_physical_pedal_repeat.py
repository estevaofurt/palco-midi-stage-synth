import unittest
import numpy as np
from types import SimpleNamespace
from wire_physical_midpoint import CoupledWire
from physical_pedal_repeat import PointDense,PointSchur
class DamperTest(unittest.TestCase):
    def make(self):
        M=np.array([[.5,.1,.03],[.1,1.,0.],[.03,0.,1.]])
        K=np.diag([100.,1000.,4000.]);D=.4*M+.001*K
        w=SimpleNamespace(M=M,K=K,D=D,P=np.array([.2,1.,.4]),port=0,U=np.eye(2),
            m=M[1:,0],k=K[1:,0],d=D[1:,0],w2=np.diag(K)[1:],gamma=np.diag(D)[1:],p=np.array([1.,.4]))
        return CoupledWire(np.array([200.,500.]),np.eye(2),np.zeros((2,1)),np.array([[.8,.2]]),[w],48000,2)
    def test_varying_damper(self):
        B=np.array([[.1],[.05]]);I=np.array([[[1.],[.4]]])
        a=PointSchur(self.make(),B,I);b=PointDense(self.make(),B,I);W=L=0.
        for t in range(120):
            d=np.array([2.*(t%13)/12]);a.set_levels(d);b.set_levels(d)
            np.testing.assert_allclose(a.compliance(),b.compliance(),rtol=1e-10,atol=1e-14)
            F=np.array([np.sin(.1*t)]);o,w,l=a.step(F);r,v,q=b.step(F)
            np.testing.assert_allclose(o,r,rtol=1e-9,atol=1e-13)
            W+=w;L+=l
        self.assertLess(abs(a.energy()+L-W)/max(abs(W),1e-30),1e-8)
        self.assertGreater(a.loss,0.)
        self.assertAlmostEqual(a.loss,b.loss,places=12)
if __name__=='__main__':unittest.main()

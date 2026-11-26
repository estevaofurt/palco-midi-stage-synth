import unittest
import numpy as np
from types import SimpleNamespace
from wire_physical_midpoint import CoupledWire
from physical_hammer_contact import Dense,Schur,Impact
from felt_law import Felt
class ContactTest(unittest.TestCase):
    def make(self):
        M=np.array([[.5,.1,.03],[.1,1.,0.],[.03,0.,1.]])
        K=np.diag([100.,1000.,4000.]);D=.4*M+.001*K
        wires=[SimpleNamespace(M=M,K=K,D=D,P=np.array([.2,1.,.4]),port=j,U=np.eye(2),
            m=M[1:,0],k=K[1:,0],d=D[1:,0],w2=np.diag(K)[1:],gamma=np.diag(D)[1:],p=np.array([1.,.4])) for j in range(2)]
        return CoupledWire(np.array([200.,500.]),np.eye(2),np.zeros((2,2)),np.array([[.8,.2],[.4,.3]]),wires,48000,2)
    def test_compliance(self):
        a=Schur(self.make());b=Dense(self.make())
        np.testing.assert_allclose(a.compliance(),b.compliance(),rtol=1e-10,atol=1e-14)
        F=np.array([1.,2.]);a.step(F);b.step(F)
        np.testing.assert_allclose(a.free(),b.free(),rtol=1e-10,atol=1e-14)
    def test_shared_mass(self):
        a=Schur(self.make());m=.01;f=Felt(1.5e8,.5e8,3000.,3.,2.5)
        b=Impact(a,[0,0],[m],[f,f],[1.])
        np.testing.assert_allclose(b.G/b.h-a.compliance(),np.full((2,2),b.h/(2*m)),rtol=1e-10,atol=1e-14)
        for _ in range(100):
            b.step()
            self.assertLess(abs(b.storage()+b.loss+b.feltloss+b.captureloss-b.initial)/b.initial,1e-8)
if __name__=='__main__':unittest.main()

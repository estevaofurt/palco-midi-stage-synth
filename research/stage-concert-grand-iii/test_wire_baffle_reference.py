import unittest
import numpy as np
from types import SimpleNamespace
from wire_physical_midpoint import CoupledWire
from wire_baffle_reference import dense_response
class WireBaffleTest(unittest.TestCase):
    def test_passive(self):
        M=np.array([[.5,.1,.03],[.1,1.,0.],[.03,0.,1.]])
        K=np.diag([100.,1000.,4000.]);D=.4*M+.001*K
        w=SimpleNamespace(M=M,K=K,D=D,P=np.array([.2,1.,.4]),port=2,U=np.eye(2),
            m=M[1:,0],k=K[1:,0],d=D[1:,0],w2=np.diag(K)[1:],gamma=np.diag(D)[1:],p=np.array([1.,.4]))
        a=CoupledWire(np.array([200.,500.]),np.eye(2),np.array([[1.,0.,0.],[0.,1.,0.]]),np.array([[.8,.2]]),[w],48000,2)
        Y,O,r=dense_response(a,(.2+.5j)*np.eye(2),np.eye(2),5.)
        self.assertTrue(r['gate'],r);self.assertGreater(r['c4AirFraction'],0.)
        self.assertAlmostEqual(r['c4AirFraction']+r['c4DryFraction'],1.,places=10)
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from types import SimpleNamespace
from wire_physical_midpoint import CoupledWire
from physical_pedal_repeat import PointSchur,PointDense
from distributed_felt import distributed_ports,damping_levels,wire_loss
class FeltTest(unittest.TestCase):
    def test_distributed(self):
        M=np.array([[.5,.1],[.1,1.]])
        K=np.diag([100.,1000.]);D=.2*M+2e-9*K
        w=SimpleNamespace(M=M,K=K,D=D,P=np.array([.2,1.]),port=0,U=np.eye(1),id='k60-s1',
            m=M[1:,0],k=K[1:,0],d=D[1:,0],w2=np.diag(K)[1:],gamma=np.diag(D)[1:],p=np.array([1.]))
        make=lambda:CoupledWire(np.array([200.,500.]),np.eye(2),np.ones((2,1)),np.array([[.8,.2]]),[w],48000,1)
        a=make();b=make();B,I,wt=distributed_ports(a,{60:dict(lengthM=.5)},.020)
        d=damping_levels([2.],wt);self.assertAlmostEqual(d.sum(),2.)
        A=PointSchur(a,B,I);R=PointDense(b,B,I);A.set_levels(d);R.set_levels(d)
        for i in range(64):
            F=np.array([1. if i<32 else 0.]);o,work,loss=A.step(F);p,wk,l=R.step(F)
            np.testing.assert_allclose(o,p,rtol=1e-9,atol=1e-12)
            self.assertAlmostEqual(loss,l,places=12)
        np.testing.assert_allclose(A.state(),R.state(),rtol=1e-9,atol=1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(R.D-R.baseD).min(),-1e-12)
        self.assertGreater(wire_loss([w],4.)[0].gamma[0],w.gamma[0])
if __name__=='__main__':unittest.main()

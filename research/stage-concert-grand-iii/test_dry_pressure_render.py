import unittest
import numpy as np
from types import SimpleNamespace
from compiled_wire_midpoint import Compiled
from dry_pressure_render import common_gain,pcm
class RenderTest(unittest.TestCase):
    def test_acceleration(self):
        M=np.array([[.5,.1],[.1,1.]])
        K=np.diag([100.,1000.]);D=.4*M+.001*K
        w=SimpleNamespace(M=M,K=K,D=D,P=np.array([.2,1.]),port=0,U=np.eye(1),
            m=M[1:,0],k=K[1:,0],d=D[1:,0],w2=np.diag(K)[1:],gamma=np.diag(D)[1:],p=np.array([1.]))
        make=lambda:Compiled(np.array([200.,500.]),np.eye(2),np.ones((2,1)),np.array([[.8,.2]]),[w],48000,1)
        a=make();b=make();F=np.ones((64,1));O=np.zeros_like(F);L=np.zeros((64,2));A=np.zeros((64,2))
        a.process(F,O,L,A)
        for j in range(len(F)):
            old=b.v.copy();b.step(F[j])
            np.testing.assert_allclose(A[j],(b.v-old)*48000,rtol=1e-10,atol=1e-9)
        np.testing.assert_array_equal(a.v,b.v)
    def test_gain(self):
        a=np.array([.1,.2]);b=np.array([1.,-2.]);g=common_gain([a,b])
        self.assertAlmostEqual(g,.4);self.assertEqual(pcm(b,g).dtype,np.int16)
if __name__=='__main__':unittest.main()

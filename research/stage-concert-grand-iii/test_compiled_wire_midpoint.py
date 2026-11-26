import unittest
import numpy as np
from types import SimpleNamespace
from compiled_wire_midpoint import Compiled,block_proof
class CompiledTest(unittest.TestCase):
    def make(self,r,n):
        M=np.array([[.5,.1,.03],[.1,1.,0.],[.03,0.,1.]])
        K=np.diag([100.,1000.,4000.]);D=.4*M+.001*K
        w=SimpleNamespace(M=M,K=K,D=D,P=np.array([.2,1.,.4]),port=0,U=np.eye(2),
            m=M[1:,0],k=K[1:,0],d=D[1:,0],w2=np.diag(K)[1:],gamma=np.diag(D)[1:],p=np.array([1.,.4]))
        return Compiled(np.array([200.,500.]),np.eye(2),np.zeros((2,1)),np.array([[.8,.2]]),[w],r,n)
    def test_equivalence(self):
        self.assertTrue(block_proof(self.make,48000,2)['gate'])
    def test_alias(self):
        a=self.make(48000,2);F=np.zeros((4,1))
        with self.assertRaises(ValueError):a.process(F,F,np.zeros((4,2)))
if __name__=='__main__':unittest.main()

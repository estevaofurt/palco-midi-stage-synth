import unittest
import numpy as np
from partitioned_acoustic_memory import PartitionedMemory,verify
class MemoryTest(unittest.TestCase):
    def test_impulse(self):
        W=np.arange(37.,dtype=float)[:,None,None]
        a=PartitionedMemory(W,8);v=np.zeros((80,1));v[0]=1.
        result=a.process(v)[:,0]
        np.testing.assert_allclose(result,np.r_[W[:,0,0],np.zeros(43)],atol=1e-11)
    def test_instantaneous_separation(self):
        W=np.array([[[2.]],[[3.]],[[4.]]])
        a=PartitionedMemory(W,2)
        np.testing.assert_allclose(a.past(),[0.])
        a.push([1.]);np.testing.assert_allclose(a.past(),[3.])
        a.push([2.]);np.testing.assert_allclose(a.past(),[10.])
    def test_reference(self):
        for m,t,B in ((2,1,8),(3,8,8),(4,31,8),(5,64,16),(3,129,32)):
            row=verify(m,t,B);self.assertTrue(row['gate'],row)
if __name__=='__main__':unittest.main()

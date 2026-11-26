import unittest
import numpy as np
from physical_acoustic_audition import PartitionedContact
from acoustic_contact import Memory
from partitioned_acoustic_memory import synthetic
class AuditionMemoryTest(unittest.TestCase):
    def test_history_and_work(self):
        U=np.eye(3);W=synthetic(3,137)
        a=PartitionedContact.__new__(PartitionedContact);b=Memory()
        a.h=b.h=1/48000;a.init_memory(U,W);b.init_memory(U,W)
        for y in np.random.default_rng(8).normal(size=(313,3)):
            x=a.memory();z=b.memory()
            np.testing.assert_allclose(x,z,atol=1e-12,rtol=1e-10)
            np.testing.assert_array_equal(x,a.memory())
            a.advance(y,x);b.advance(y,z)
        self.assertAlmostEqual(a.air,b.air,places=12)
    def test_dry(self):
        a=PartitionedContact.__new__(PartitionedContact);a.h=1/48000
        a.init_memory(np.eye(2),np.zeros((1,2,2)))
        for y in ([1.,2.],[3.,4.]):
            a.advance(np.array(y),a.memory())
        self.assertEqual(a.air,0.);np.testing.assert_array_equal(a.memory(),[0.,0.])
if __name__=='__main__':unittest.main()

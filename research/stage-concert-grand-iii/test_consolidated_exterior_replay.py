import unittest
import numpy as np
from consolidated_exterior_replay import apply_remaining,require,FREQ
class ConsolidationTest(unittest.TestCase):
    def test_replacement(self):
        n=len(FREQ);w=2*np.pi*np.asarray(FREQ);scale=1.204*w[:,None,None]/(4*np.pi)
        X=np.tile(np.eye(2),(n,1,1));Z=np.ones((n,4,4),complex)
        Z[:,:2,:2].imag=scale*X;Z[:,2:,2:].imag=scale*X
        old=Z.copy();vals=np.stack([X,X*1.001,X*1.002])
        rows=apply_remaining(Z,old,{'block_0_0':vals},[(0,0)],'self',w,count=2)
        self.assertTrue(rows[0]['gate']);np.testing.assert_array_equal(Z.real,old.real)
        np.testing.assert_allclose(Z[:,:2,:2].imag,scale*vals[-1])
        np.testing.assert_array_equal(Z[:,2:,:],old[:,2:,:])
        with self.assertRaises(ValueError):apply_remaining(Z,old,{'block_0_0':vals},[(0,0)],'self',w,count=2)
    def test_guard(self):
        with self.assertRaises(ValueError):require({},30,'a'*64,{})
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from lid_exterior import Panel
from shared_edge_modal_replay import edge_pairs,replace_block,require_edge_proof
class ReplayTest(unittest.TestCase):
    def test_block(self):
        Z=np.ones((2,6,6),complex)*(2+3j);ref=Z.copy();X=np.arange(8.).reshape(2,2,2);w=np.array([4.,8.])
        replace_block(Z,0,2,X,w,rho=1.,count=2)
        np.testing.assert_array_equal(Z.real,ref.real)
        np.testing.assert_allclose(Z[:,:2,4:].imag,X*w[:,None,None]/(4*np.pi))
        np.testing.assert_array_equal(Z[:,4:,:2],Z[:,:2,4:].transpose(0,2,1))
        np.testing.assert_array_equal(Z[:,2:4],ref[:,2:4])
        with self.assertRaises(ValueError):replace_block(Z,0,0,X,w,count=2)
    def test_edges(self):
        x=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]])
        n=np.array([0.,0.,1.]);p=[Panel(x,n,3),Panel(x+[1,0,0],n,3),Panel(x+[2,1,0],n,3)]
        self.assertEqual(edge_pairs(p),[(0,1)])
    def test_guard(self):
        with self.assertRaises(ValueError):require_edge_proof({},30,'a'*64)
if __name__=='__main__':unittest.main()

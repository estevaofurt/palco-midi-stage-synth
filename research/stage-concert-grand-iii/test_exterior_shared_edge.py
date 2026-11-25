import unittest
import numpy as np
from lid_exterior import Panel
from exterior_shared_edge import edge_duffy,corrected_pair,shared_edge,tensor_triangle
from exterior_pair_stream import pair_integrals
from split_radiation import relative
class EdgeTest(unittest.TestCase):
    def fixture(self,count):
        a=np.array([[0.,0.,0.],[1.,0.,0.],[.6,.7,0.]])
        b=np.array([[0.,0.,0.],[1.,0.,0.],[.4,0.,.8]])
        return Panel(a,np.array([0.,0.,1.]),count),Panel(b,np.array([0.,-1.,0.]),count)
    def test_area_and_reciprocity(self):
        p,q=self.fixture(3);k=np.array([.55,2.7])
        r,x,s=edge_duffy(p,q,k,10);rr,xx,_=edge_duffy(q,p,k,10)
        self.assertLess(relative(r,rr.transpose(0,2,1)),1e-10)
        # Parameter partitions are not identical after swapping surfaces.
        self.assertLess(relative(x,xx.transpose(0,2,1)),.002)
        self.assertAlmostEqual(s['areaProduct'],s['expectedAreaProduct'],places=12)
        r2,x2,_=edge_duffy(p,q,k,16)
        self.assertLess(relative(x,x2),.002)
        self.assertLess(relative(r,r2),1e-9)
    def test_smooth_kernel_preserved(self):
        p,q=self.fixture(6);k=np.array([.55,2.7])
        r,x,_=corrected_pair(p,q,k,14,14,block=32)
        _,a,w,A=p.samples(14);_,b,v,B=q.samples(14)
        ref,old,_=pair_integrals(a,w[:,None]*A,b,v[:,None]*B,k,mutual=True,block=32)
        self.assertLess(relative(r,ref),1e-10)
        self.assertTrue(np.isfinite(x).all())
if __name__=='__main__':unittest.main()

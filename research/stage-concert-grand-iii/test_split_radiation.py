import unittest
import numpy as np
from board_contour import hull
from radiation_impedance import impedance
from split_radiation import split_load,fan_batch
from polygon_radiation import response
class SplitTest(unittest.TestCase):
    def setUp(self):
        self.poly=hull([[0,0],[.4,0],[.4,.5],[0,.5]])
        self.field=lambda xy,poly=None:np.c_[np.ones(len(xy)),xy[:,0],xy[:,1]]
        self.mic=[[.2,.25,.17],[.1,.1,.17]]
    def test_batch(self):
        _,_,_,q=fan_batch(self.poly,self.field,[80.,250.],1.204,343.,12,18)
        for i,f in enumerate([80.,250.]):
            z=impedance(self.poly,self.field,2j*np.pi*f,1.204,343.,12,18)
            np.testing.assert_allclose(q[i],z,rtol=1e-12,atol=1e-12)
    def test_gram(self):
        rows=split_load(self.poly,self.field,[80.,250.],self.mic,12,18,16)
        for z,h,r in rows:
            self.assertTrue(r['gate']);self.assertLess(r['gramVsSurface'],1e-10)
            self.assertGreaterEqual(min(np.linalg.eigvalsh(z.real)),-1e-10)
            self.assertEqual(h.shape,(2,3))
    def test_nested_projection(self):
        z,h,r=split_load(self.poly,self.field,[80.],self.mic,12,18,16)[0]
        q,g,_=split_load(self.poly,lambda xy,p=None:self.field(xy,p)[:,:2],[80.],self.mic,12,18,16)[0]
        np.testing.assert_allclose(z[:2,:2],q,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(h[:,:2],g,rtol=1e-12,atol=1e-12)
    def test_power(self):
        z,h,_=split_load(self.poly,self.field,[80.],self.mic,12,18,16)[0]
        m=dict(M=np.eye(3),K=np.diag([1e5,2e5,3e5]),D=np.eye(3),P=np.eye(3))
        _,_,r=response(m,z,h,80.)
        self.assertLess(r['powerRelative'],1e-12);self.assertLess(r['reciprocity'],1e-12)
        self.assertTrue(0<r['airPowerFraction']<1)
if __name__=='__main__':unittest.main()

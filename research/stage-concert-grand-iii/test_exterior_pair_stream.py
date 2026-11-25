import unittest
import numpy as np
from scipy.spatial.distance import cdist
from exterior_pair_stream import pair_integrals
from lid_exterior import Panel,load
from split_radiation import relative
class PairStreamTest(unittest.TestCase):
    def test_block_equivalence(self):
        rng=np.random.default_rng(85);x=rng.random((117,3));y=rng.random((93,3))+2
        A=rng.normal(size=(len(x),8));B=rng.normal(size=(len(y),6));k=np.array([.55,1.5,5.5])
        D=cdist(x,y)
        R=np.stack([A.T@(np.sinc(f*D/np.pi)@B) for f in k])
        X=np.stack([A.T@((np.cos(f*D)/D)@B) for f in k])
        for b in (1,7,32,128):
            r,q,s=pair_integrals(x,A,y,B,k,mutual=True,block=b)
            self.assertLess(relative(R,r),1e-12);self.assertLess(relative(X,q),1e-12)
            self.assertEqual(s['blockedDistanceBytes'],min(b,len(x))*len(y)*8)
        r,q,s=pair_integrals(x,A,x,A,k,mutual=False,block=16)
        self.assertIsNone(q);np.testing.assert_allclose(r,r.transpose(0,2,1),atol=1e-10)
        with self.assertRaises(ValueError):pair_integrals(x,A,x,A,k,mutual=True)
    def test_full_load(self):
        x=np.array([[0.,0.,0.],[1.,0.,0.],[1.,.7,0.],[0.,.8,0.]])
        p=[Panel(x,np.array([0.,0.,1.]),6),Panel(x+[0.,0.,.5],np.array([0.,0.,1.]),6)]
        a=load(p,[30.,150.],8,14,16);b=load(p,[30.,150.],8,14,16,pair_block=17)
        for (Z,r),(Q,s) in zip(a,b):
            self.assertLess(relative(Z,Q),1e-12)
            for key in ('gramVsSurface','reactiveAsymmetry','passivityMinRelative','reciprocity'):
                self.assertAlmostEqual(r[key],s[key],places=12)
            self.assertEqual(r['gate'],s['gate'])
    def test_extended_basis_pair(self):
        x=np.array([[0.,0.,0.],[1.,0.,0.],[1.,.7,0.],[0.,.8,0.]])
        p=Panel(x,np.array([0.,0.,1.]),36)
        _,y,w,V=p.samples(12);A=w[:,None]*V;k=np.array([.55,2.7])
        r,_,s=pair_integrals(y,A,y,A,k,mutual=False,block=32)
        D=cdist(y,y);R=np.stack([A.T@(np.sinc(f*D/np.pi)@A) for f in k])
        self.assertLess(relative(r,R),1e-12)
        self.assertLess(s['blockedDistanceBytes'],s['fullDistanceBytes']/10)
if __name__=='__main__':unittest.main()

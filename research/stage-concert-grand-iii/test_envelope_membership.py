import unittest
import numpy as np
from envelope_membership import clearance,internal_exact
from neumann_envelope import envelope
from inclined_lid import build
class EnvelopeMembershipTest(unittest.TestCase):
    def test_nonconvex_union(self):
        poly=np.array([[0.,0.],[1.,-.5],[1.,.5]])
        p=np.array([[.5,.24,.05],[.5,.26,.05],[.5,.1,.7],[.5,.1,-.01]])
        d=clearance(poly,.24,30,p)
        self.assertTrue(d[0]>0)
        self.assertTrue(np.all(d[1:]<0))
        surf,ports,c=envelope(poly,.24,30,1,lambda x:np.ones((len(x),1)))
        rejected=any(((p[:1]-s['panel'].origin)@s['normal']>=0).any() for s in surf)
        self.assertTrue(rejected)
        q,r=internal_exact(poly,.24,30,surf,ports,c,3,.94)
        self.assertTrue(np.isfinite(q).all())
        self.assertEqual(r['outsideOrBoundary'],int(sum(clearance(poly,.24,30,q)<=1e-10)))
    def test_independent_tetrahedra(self):
        poly=np.array([[0.,0.],[1.,-.5],[1.,.5]])
        rng=np.random.default_rng(531)
        pts=rng.uniform([-.1,-.6,-.1],[1.1,.6,1.15],(240,3))
        for a in (30,55):
            model,_,_=build(poly,8,3,.24,a,lambda x:np.ones((len(x),1)))
            tet=model['xyz'][model['tet']]
            inv=np.linalg.inv(np.transpose(tet[:,1:]-tet[:,:1],(0,2,1)))
            actual=[]
            for q in pts:
                v=np.einsum('tij,tj->ti',inv,q-tet[:,0])
                lam=np.c_[1-v.sum(1),v]
                actual.append(bool(np.any(lam.min(1)>-1e-10)))
            np.testing.assert_array_equal(clearance(poly,.24,a,pts)>0,actual)
    def test_interface_and_boundary(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        q=np.array([[.5,.5,.24],[.5,.5,0.],[.5,1.,.1],[.5,.5,.24+.5]])
        d=clearance(poly,.24,45,q)
        self.assertGreater(d[0],0.)
        np.testing.assert_allclose(d[1:],0.,atol=1e-12)
if __name__=='__main__':unittest.main()

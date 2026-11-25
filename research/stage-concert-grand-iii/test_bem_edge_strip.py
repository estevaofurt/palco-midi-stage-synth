import unittest
import numpy as np
from exterior_bem import elements,topology
from test_exterior_bem import sphere
from bem_edge_strip import refine_strips,budget_strips
class StripTest(unittest.TestCase):
    def test_aligned_strip_and_neighbors(self):
        t=sphere(.5,0);labels=np.arange(len(t));sel=np.full(len(t),-1,int);sel[0]=0
        q,l,parent,r=refine_strips(t,labels,sel,.25)
        self.assertTrue(r['gate']);self.assertEqual(r['alignedStrips'],1)
        self.assertTrue(topology(q)['gate'])
        a,b,c=t[0];x=.75*a+.25*c;y=.75*b+.25*c
        np.testing.assert_allclose(q[parent==0],[[a,b,y],[a,y,x],[x,y,c]],atol=1e-14)
        np.testing.assert_allclose(np.bincount(l,weights=elements(q)[2]),elements(t)[2],atol=1e-12)
        np.testing.assert_array_equal(l,labels[parent])
    def test_conflicting_requests_conform(self):
        t=sphere(.5,0);labels=np.arange(len(t))
        for j in range(3):
            q,l,p,r=refine_strips(t,labels,np.full(len(t),j,int))
            self.assertTrue(topology(q)['gate']);self.assertLess(r['areaRelative'],1e-9)
        self.assertGreater(len(q),len(t))
    def test_budget_and_rejection(self):
        t=sphere(.5,1);l=np.arange(len(t));S=np.arange(1.,3*len(t)+1).reshape(-1,3);M=np.ones_like(S,bool)
        q,ll,p,r=budget_strips(t,l,S,M,60)
        self.assertLessEqual(len(q),60);self.assertGreater(len(q),len(t))
        self.assertGreater(r['capturedSelectedIndicator'],0.)
        with self.assertRaises(ValueError):budget_strips(t,l,S,np.zeros_like(M),60)
        with self.assertRaises(ValueError):budget_strips(t,l,S,M,len(t))
        with self.assertRaises(ValueError):refine_strips(t,l,np.full(len(t),-1,int))
if __name__=='__main__':unittest.main()

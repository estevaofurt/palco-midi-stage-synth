import unittest
import numpy as np
from test_exterior_bem import sphere
from bem_linear import COL,CHECK,fit,targets
from bem_linear_adaptive import MARK,indicator,budget_refine
from exterior_bem import topology,elements
class LinearAdaptiveTest(unittest.TestCase):
    def test_disjoint_and_indicator(self):
        for x in MARK:
            self.assertFalse(any(np.allclose(x,y) for y in np.vstack([COL,CHECK])))
        t=sphere(.5,1);k=2*np.pi*80/343.
        q,r=fit(t,np.ones((3*len(t),1)),k,5)
        scores=indicator(t,q,np.ones((len(t)*len(MARK),1)),k,6)
        self.assertEqual(scores.shape,(len(t),));self.assertTrue(np.isfinite(scores).all())
        self.assertGreater(scores.sum(),0.)
    def test_budget_and_geometry(self):
        t=sphere(.5,1);labels=np.arange(len(t));scores=np.arange(1.,len(t)+1)
        q,l,r=budget_refine(t,labels,scores,60)
        self.assertGreater(len(q),len(t));self.assertLessEqual(len(q),60)
        self.assertTrue(topology(q)['gate'])
        self.assertAlmostEqual(topology(q)['volume'],topology(t)['volume'],places=12)
        np.testing.assert_allclose(np.bincount(l,weights=elements(q)[2]),elements(t)[2],atol=1e-12)
        self.assertGreater(r['capturedIndicator'],0.)
if __name__=='__main__':unittest.main()

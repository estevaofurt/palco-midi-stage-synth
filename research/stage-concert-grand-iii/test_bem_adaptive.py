import unittest
import numpy as np
from test_exterior_bem import sphere
from exterior_bem import topology,elements
from bem_adaptive import refine,mark
class AdaptiveTest(unittest.TestCase):
    def test_single_mark_and_labels(self):
        t=sphere(.5,1);lab=np.arange(len(t));mask=np.zeros(len(t),bool);mask[0]=True
        q,l=refine(t,lab,mask)
        self.assertTrue(topology(q)['gate'])
        self.assertGreater(len(q),len(t));self.assertLess(len(q),4*len(t))
        np.testing.assert_allclose(topology(q)['volume'],topology(t)['volume'],atol=1e-12)
        a=elements(t)[2];b=elements(q)[2]
        np.testing.assert_allclose(np.bincount(l,weights=b),a,atol=1e-12)
    def test_marking(self):
        score=np.array([.1,5.,.2,10.,.5])
        np.testing.assert_array_equal(mark(score),[False,False,False,True,False])
        self.assertEqual(sum(mark(np.ones(10))),4)
if __name__=='__main__':unittest.main()

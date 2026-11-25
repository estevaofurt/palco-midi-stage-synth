import unittest
import numpy as np
from bem_p1_priority import scores,contribution
from bem_linear import targets
from bem_linear_adaptive import MARK
from bem_p1_stream import fit
from bem_linear import COL
from test_exterior_bem import sphere
class PriorityTest(unittest.TestCase):
    def test_worst_weight(self):
        A=np.array([[.4,0.,0.],[0.,.25,.25]])
        s,r=scores([A],'balanced');self.assertGreater(s[1],s[0])
        s,r=scores([A],'worst');self.assertGreater(s[0],s[1])
        self.assertAlmostEqual(r['worstColumnResidual'],np.sqrt(.4))
    def test_contribution(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        x,n,w,o=targets(t,COL);V=np.c_[np.ones(len(x)),x[:,0]]
        q,_=fit(t,V,k,4)
        x,n,w,o=targets(t,MARK);V=np.c_[np.ones(len(x)),x[:,0]]
        A=contribution(t,q,V,k,5)
        self.assertEqual(A.shape,(len(t),2))
        self.assertTrue(np.isfinite(A).all())
        self.assertTrue(np.all(A>=0))
        with self.assertRaises(ValueError):contribution(t,q,V*0,k,5)
if __name__=='__main__':unittest.main()

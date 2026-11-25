import unittest
import numpy as np
from lid_exterior import Panel
from enriched_aperture_reference import enrich,restrict
from enriched_smooth_diagnostic import require_sources
class EnrichedReferenceTest(unittest.TestCase):
    def test_nested_indices(self):
        t=np.array([[0.,0.,0.],[1.,0.,0.],[.4,.7,0.]])
        q=np.array([[0.,0.,0.],[1.,0.,0.],[.9,.7,0.],[.1,.7,0.]])
        n=np.array([0.,0.,1.]);old=[Panel(t if i<2 else q,n,55) for i in range(7)]
        pp,counts,idx,checks=enrich(old)
        self.assertEqual(counts,[61,61,63,63,63,63,55])
        self.assertEqual(len(checks),6);self.assertIs(pp[-1].basis,old[-1].basis)
        A=np.arange(429*429).reshape(429,429)
        np.testing.assert_array_equal(restrict(A,idx),A[np.ix_(idx,idx)])
        for a,b in zip(old,pp):
            x,_,_,_=a.samples(12)
            np.testing.assert_allclose(a.basis(x),b.basis(x)[:,:55],rtol=1e-13,atol=1e-12)
    def test_invalid(self):
        with self.assertRaises(ValueError):enrich([])
        with self.assertRaises(ValueError):require_sources({}, {},30,'a'*64)
if __name__=='__main__':unittest.main()

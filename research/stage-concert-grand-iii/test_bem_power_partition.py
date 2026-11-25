import unittest
import numpy as np
from bem_power_partition import partition,audit
from bem_linear import fit
from test_exterior_bem import sphere
class PartitionTest(unittest.TestCase):
    def test_exact_partition_and_cancellation(self):
        F=np.diag([2.,3.]);E=np.array([[.2,.1j],[-.1j,-.3]])
        r=partition(F,F+E,F)
        self.assertAlmostEqual(r['totalPowerRelative'],0.)
        self.assertAlmostEqual(r['boundaryWorkRelative'],r['computedWorkRelative'])
        self.assertAlmostEqual(r['errorAlignment'],-1.)
        self.assertLess(r['partitionClosure'],1e-14)
        r=partition(F+E,F,F)
        self.assertAlmostEqual(r['computedWorkRelative'],0.)
        self.assertAlmostEqual(r['boundaryWorkRelative'],r['totalPowerRelative'])
    def test_sphere_work(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        q,_=fit(t,np.ones((3*len(t),1)),k,6)
        v=lambda x,owner:np.ones((len(x),1))
        P,C,F,r=audit(t,q,v,k,4,7,angular=24,source_order=7)
        self.assertLess(r['partitionClosure'],1e-12)
        self.assertGreater(F[0,0].real,0.)
        self.assertGreater(C[0,0].real,0.)
        self.assertLess(r['computedWorkRelative'],.15,r)
        self.assertTrue(np.isfinite(P).all())
if __name__=='__main__':unittest.main()

import unittest,math
import numpy as np
from bem_edge_audit import edge_samples
from bem_power_partition import integrate,partition
from bem_p1_static_moments import fit,operators
from bem_linear import far_gram
from test_exterior_bem import sphere
class EdgeAuditTest(unittest.TestCase):
    def test_positive_exact_moments(self):
        t=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]])
        x,w=edge_samples(t,7);self.assertEqual(x.shape,(1,147,3))
        self.assertTrue(np.all(w>0));self.assertTrue(np.all(x[:,:,0]>0))
        self.assertTrue(np.all(x[:,:,1]>0));self.assertTrue(np.all(x[:,:,0]+x[:,:,1]<1))
        for i in range(5):
            for j in range(5-i):
                exact=math.factorial(i)*math.factorial(j)/math.factorial(i+j+2)
                self.assertAlmostEqual(float(np.sum(w*x[:,:,0]**i*x[:,:,1]**j)),exact,places=13)
    def test_vertex_permutation(self):
        t=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]])
        x,w=edge_samples(t,6);y,v=edge_samples(t[:,[1,2,0]],6)
        np.testing.assert_allclose(np.roll(x,-36,axis=1),y,atol=1e-14)
        np.testing.assert_allclose(np.roll(w,-36,axis=1),v,atol=1e-14)
    def test_fixed_density_work(self):
        t=sphere(.5,0);k=2*np.pi*80/343.
        v=lambda x,o:np.ones((len(x),1))
        q,r=fit(t,k,4,6,v)
        P,C,rep=integrate(t,q,v,k,5,7,operator=operators,sample_rule=edge_samples)
        F=1.204*343*k*k/(4*np.pi)*far_gram(t,q,k,order=24,surface_order=7)
        m=partition(P,C,F)
        self.assertLess(m['partitionClosure'],1e-12)
        self.assertGreater(C[0,0].real,0.)
        self.assertTrue(np.isfinite(P).all())
        self.assertLess(m['computedWorkRelative'],.20)
if __name__=='__main__':unittest.main()

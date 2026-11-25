import unittest
import numpy as np
from test_exterior_bem import sphere
from bem_edge_localization import inventory,summarize,localize
from bem_p1_static_moments import fit
from bem_power_partition import integrate
from bem_p1_static_moments import operators
from bem_edge_audit import edge_samples
class EdgeLocalizationTest(unittest.TestCase):
    def test_physical_and_artificial_edges(self):
        from recess_envelope import build
        from bem_envelope import triangulate
        p=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        f=lambda x:np.ones((len(x),1))
        s,ports,c,r=build(p,.24,-.18,30,3,f,3)
        t,l,_=triangulate(s,1);C,A=inventory(t,l,[v['kind'] for v in s])
        self.assertIn('mesh-edge',C);self.assertIn('crease-port-transition',C)
        self.assertTrue(np.all(A[C=='mesh-edge']<=1e-5))
        self.assertTrue(np.all(A[C=='crease-port-transition']>1e-5))
        with self.assertRaises(ValueError):inventory(t[:-1],l[:-1],[v['kind'] for v in s])
    def test_partition(self):
        C=np.array([['crease','mesh-edge','mesh-edge']])
        E=np.zeros((1,3,3,2));E[0,0,0]=[3.,4.];E[0,1,1]=[1.,2.]
        T=np.ones_like(E);A=np.ones(E.shape[:3])
        r=summarize(C,E,T,A)
        self.assertAlmostEqual(r['heldoutResidual'],np.sqrt(10/18))
        self.assertAlmostEqual(r['heldoutWorstColumn'],np.sqrt(6/9))
        self.assertAlmostEqual(r['categories'][0]['residualEnergyFraction'],.7)
        self.assertAlmostEqual(r['categories'][0]['bandEnergyFractions'][0],.7)
        self.assertLess(r['energyClosure'],1e-14)
    def test_matches_independent_integral(self):
        t=sphere(.5,0);labels=np.zeros(len(t),int);k=2*np.pi*80/343.
        v=lambda x,o:np.c_[np.ones(len(x)),x[:,0]]
        q,_=fit(t,k,4,5,v)
        r=localize(t,labels,['port'],q,v,k,4,5)
        _,_,a=integrate(t,q,v,k,4,5,operator=operators,sample_rule=edge_samples)
        self.assertAlmostEqual(r['heldoutResidual'],a['heldoutResidual'],places=12)
        self.assertAlmostEqual(r['heldoutWorstColumn'],a['heldoutWorstColumn'],places=12)
        self.assertLess(r['energyClosure'],1e-12)
if __name__=='__main__':unittest.main()

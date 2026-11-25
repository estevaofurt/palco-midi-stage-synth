import unittest
import numpy as np
from lid_exterior import Panel
from edge_enriched_flux import EdgeEnrichedFlux
class EnrichedTest(unittest.TestCase):
    def test_nested_mass(self):
        for x in (np.array([[0.,0.,0.],[1.,0.,0.],[.4,.7,0.]]),
                  np.array([[0.,0.,0.],[2.,0.,0.],[1.6,.3,0.],[.2,.7,0.]])):
            p=Panel(x,np.array([0.,0.,1.]),55)
            for width in (.03,.06):
                q=EdgeEnrichedFlux(p.poly,p.basis,width)
                r=q.audit()
                self.assertLess(r['massRelative'],1e-8)
                self.assertLess(r['maximumIntegralError'],1e-8)
                self.assertLess(r['baselineRelative'],1e-14)
                self.assertEqual(q.extraCount,2*len(p.poly))
    def test_invalid(self):
        p=Panel(np.array([[0.,0.,0.],[1.,0.,0.],[.4,.7,0.]]),np.array([0.,0.,1.]),55)
        with self.assertRaises(ValueError):EdgeEnrichedFlux(p.poly,p.basis,0.)
if __name__=='__main__':unittest.main()

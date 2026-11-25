import unittest
import numpy as np
from test_exterior_bem import sphere
from bem_edge_strip import refine_strips
from bem_mesh_guard import signature
from bem_candidate_guard import validate_candidate
class CandidateTest(unittest.TestCase):
    def test_refinement_and_tampering(self):
        t=sphere(.5,0);l=np.arange(len(t));sel=np.full(len(t),-1,int);sel[0]=0
        tt,ll,parents,r=refine_strips(t,l,sel)
        budget=100;r.update(elementBudget=budget,meshSha256=signature(tt,ll))
        self.assertTrue(validate_candidate(t,l,tt,ll,parents,r,budget)['gate'])
        with self.assertRaises(ValueError):validate_candidate(t,l,tt,ll,parents,dict(r,meshSha256='x'),budget)
        wrong=parents.copy();wrong[0]=(wrong[0]+1)%len(t)
        with self.assertRaises(ValueError):validate_candidate(t,l,tt,ll,wrong,r,budget)
        with self.assertRaises(ValueError):validate_candidate(t,l,tt,ll,parents,r,len(t))
if __name__=='__main__':unittest.main()

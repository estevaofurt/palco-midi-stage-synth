import unittest
import numpy as np
from hybrid_cavity import build,response
from graded_cavity_replay import require_sources
from split_radiation import relative
class GradedCavityTest(unittest.TestCase):
    def test_graded_solvers(self):
        poly=np.array([[0.,0.],[1.,0.],[1.2,.7],[.7,1.5],[0.,1.]])
        field=lambda x:np.c_[np.ones(len(x)),x[:,0]]
        for angle in (30,55):
            m=build(poly,8,1,.24,angle,field,6,wedge_layers=4,boundary_n=16,edge_grading=.5,layer_grading=.5)
            for f in (30.,150.):
                z,p,r=response(m,f,[[.3,.5,.12]],solver='dense')
                Z,P,R=response(m,f,[[.3,.5,.12]],solver='schur-real')
                self.assertTrue(r['gate'] and R['gate'])
                self.assertLess(relative(z,Z),1e-8);self.assertLess(relative(p,P),1e-8)
    def test_guard(self):
        with self.assertRaises(ValueError):require_sources({}, {}, {},30,'a'*64)
if __name__=='__main__':unittest.main()

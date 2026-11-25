import unittest
import numpy as np
from wedge_surface_trace import graded_fractions,surface_panels
from graded_edge_trace_diagnostic import geometry_check,require_source
from acoustic_trace_resolution import surface_mass
class GradedTest(unittest.TestCase):
    def test_fractions(self):
        t=graded_fractions(20,0.);q=graded_fractions(20,.85)
        np.testing.assert_array_equal(t,np.arange(21)/20)
        np.testing.assert_allclose(q,1-q[::-1],atol=1e-15)
        self.assertLess(q[1],t[1]);self.assertGreater(np.diff(q).min(),0.)
        for s in (-.1,1.1,float('nan')):
            with self.assertRaises(ValueError):graded_fractions(20,s)
    def test_geometry(self):
        poly=np.array([[0.,0.],[2.,0.],[2.,1.],[0.,1.]])
        old=surface_panels(poly,12,55,.24,8,55)
        new=surface_panels(poly,12,55,.24,8,55,edge_grading=.5,layer_grading=.85)
        self.assertEqual(geometry_check(old,new),sum(len(v[2]) for v in old))
        for p,x,f,m in new:
            _,_,A=surface_mass(x,f);self.assertAlmostEqual(A,p.basis.area,places=10)
    def test_archive(self):
        with self.assertRaises(ValueError):require_source({},30,'a'*64)
if __name__=='__main__':unittest.main()

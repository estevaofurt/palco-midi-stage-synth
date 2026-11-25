import unittest
import numpy as np
from closed_cavity import mesh
from inclined_lid import build
from hybrid_cavity import build as hybrid,response
from lid_exterior import ports
from acoustic_trace_resolution import panel_capture
from wedge_surface_trace import surface_panels,surface_capture
from nested_acoustic_ports import embedding
class BoundaryRefinementTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.2,.7],[.7,1.5],[0.,1.]])
        self.field=lambda x:np.c_[np.ones(len(x)),x[:,0]]
    def test_default_and_cost(self):
        a=mesh(self.poly,10,1,.24);b=mesh(self.poly,10,1,.24,boundary_n=10)
        for x,y in zip(a,b):np.testing.assert_array_equal(x,y)
        c=mesh(self.poly,10,1,.24,boundary_n=30);d=mesh(self.poly,30,1,.24)
        self.assertLess(len(c[0]),len(d[0]));self.assertGreater(len(c[0]),len(a[0]))
        with self.assertRaises(ValueError):mesh(self.poly,10,1,.24,boundary_n=9)
    def test_surface_equivalence(self):
        for angle in (30,55):
            m,C0,r=build(self.poly,10,1,.24,angle,self.field,wedge_layers=4,boundary_n=30)
            pp,C=ports(m,C0,r,21,canonical=True)
            for i,((p,x,f,d),v,ff) in enumerate(zip(surface_panels(self.poly,30,angle,.24,4,21),pp,m['apertureFaces'])):
                G,n=surface_capture(p,x,f);H,k=panel_capture(m['xyz'],ff,C[:,21*i:21*(i+1)],v)
                T,_=embedding([p],[v]);self.assertEqual(n,k);self.assertEqual(len(f),len(ff))
                np.testing.assert_allclose(T.T@G@T,H,atol=1e-9)
            self.assertEqual(r['boundaryN'],30)
    def test_hybrid_equivalence(self):
        m=hybrid(self.poly,10,1,.24,30,self.field,10,wedge_layers=3,boundary_n=24)
        for f in (30.,150.):
            Z,P,r=response(m,f,[[.3,.5,.12]],solver='dense')
            z,p,rr=response(m,f,[[.3,.5,.12]],solver='schur')
            self.assertTrue(r['gate'] and rr['gate'])
            np.testing.assert_allclose(Z,z,rtol=1e-8,atol=1e-8)
            np.testing.assert_allclose(P,p,rtol=1e-8,atol=1e-8)
if __name__=='__main__':unittest.main()

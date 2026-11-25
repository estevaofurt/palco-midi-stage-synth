import unittest
import numpy as np
from lid_exterior import Panel,ports
from nested_acoustic_ports import embedding
from wedge_surface_trace import surface_panels,surface_capture
from inclined_lid import build
from acoustic_trace_resolution import panel_capture
from lower_prism import build as lower_build
from split_radiation import relative
class HighFluxTest(unittest.TestCase):
    def test_nested_bases(self):
        for xy in (np.array([[0.,0.],[2.,.01],[1.8,.031]]),np.array([[0.,0.],[1.,0.],[1.2,.8],[0.,1.]])):
            x=np.c_[xy,np.zeros(len(xy))];n=np.array([0.,0.,1.]);p=Panel(x,n,55)
            _,_,w,V=p.samples(18)
            np.testing.assert_allclose(p.basis.area*V.T@(w[:,None]*V),np.eye(55),atol=1e-8)
            for count in (28,36,45,55):
                q=Panel(np.roll(x,1,axis=0),n,count);T,r=embedding([p],[q],order=18)
                self.assertTrue(r['gate']);self.assertEqual(T.shape,(55,count))
    def test_upper_trace_parity(self):
        poly=np.array([[0.,0.],[1.,0.],[1.2,.7],[.7,1.5],[0.,1.]])
        field=lambda x:np.ones((len(x),1))
        m,C0,r=build(poly,8,1,.24,55,field,wedge_layers=4,boundary_n=16)
        panels,C=ports(m,C0,r,55,canonical=True)
        for i,((p,x,f,d),q,ff) in enumerate(zip(surface_panels(poly,16,55,.24,4,55),panels,m['apertureFaces'])):
            G,n=surface_capture(p,x,f);H,k=panel_capture(m['xyz'],ff,C[:,55*i:55*(i+1)],q)
            T,_=embedding([p],[q],order=18)
            self.assertEqual(n,k);self.assertLess(relative(T.T@G@T,H),1e-8)
    def test_lower_trace_projection(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,.7],[0.,1.]])
        f=lambda x:np.ones((len(x),1))
        hi=lower_build(poly,10,.18,f,55);lo=lower_build(poly,10,.18,f,36)
        T,_=embedding([hi['mouth']],[lo['mouth']],order=18)
        self.assertLess(relative(hi['B'][:,1:]@T,lo['B'][:,1:]),1e-8)
if __name__=='__main__':unittest.main()

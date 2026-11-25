import unittest
import numpy as np
from inclined_lid import build
from lid_exterior import ports
from acoustic_trace_resolution import panel_capture,describe
from nested_acoustic_ports import embedding
from wedge_surface_trace import surface_panels,surface_capture
class SurfaceTraceTest(unittest.TestCase):
    def test_matches_volume_trace(self):
        poly=np.array([[0.,0.],[1.,0.],[1.2,.7],[.7,1.5],[0.,1.]])
        field=lambda x:np.ones((len(x),1))
        for angle in (30,55):
            for k in (1,4):
                model,C0,r=build(poly,12,1,.24,angle,field,wedge_layers=k)
                pp,C=ports(model,C0,r,21,canonical=True)
                ss=surface_panels(poly,12,angle,.24,k,21)
                self.assertEqual(len(ss),len(pp))
                for i,((p,x,f,div),a,ff) in enumerate(zip(ss,pp,model['apertureFaces'])):
                    G,n=surface_capture(p,x,f)
                    H,m=panel_capture(model['xyz'],ff,C[:,21*i:21*(i+1)],a)
                    T,_=embedding([p],[a])
                    self.assertEqual(n,m);self.assertEqual(len(f),len(ff))
                    np.testing.assert_allclose(T.T@G@T,H,atol=1e-9)
    def test_refine_both_directions(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        def worst(n,k):
            return min(describe(surface_capture(p,x,f)[0])['minimumCapturedEnergy']
                for p,x,f,_ in surface_panels(poly,n,30,.24,k,36))
        self.assertGreater(worst(40,16),worst(8,2)+.5)
if __name__=='__main__':unittest.main()

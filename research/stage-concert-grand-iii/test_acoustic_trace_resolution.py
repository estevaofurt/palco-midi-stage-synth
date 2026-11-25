import unittest
import numpy as np
from lid_exterior import Panel,ports
from inclined_lid import build
from acoustic_trace_resolution import surface_mass,capture,describe,panel_capture
from nested_acoustic_ports import embedding
class TraceTest(unittest.TestCase):
    def test_exact_linear_and_unresolved_quadratic(self):
        xyz=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
        faces=np.array([[0,1,2]]);nodes,M,A=surface_mass(xyz,faces)
        C=M@np.ones((3,1))/A
        self.assertAlmostEqual(describe(capture(M,C,A))['minimumCapturedEnergy'],1.)
        panel=Panel(xyz,np.array([0.,0.,1.]),6)
        _,x,w,V=panel.samples(12);L=np.c_[1-x[:,0]-x[:,1],x[:,0],x[:,1]]
        G,n=panel_capture(xyz,faces,L.T@(w[:,None]*V),panel)
        lo=Panel(xyz,np.array([0.,0.,1.]),3);T,_=embedding([panel],[lo])
        self.assertLess(describe(G,T)['worstProjectionResidual'],1e-6)
        self.assertEqual(describe(G)['nearNullModes'],3)
    def test_wedge_trace_independent_of_prism_layers(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,.7],[0.,1.]])
        field=lambda x:np.ones((len(x),1))
        gs=[]
        for nz in (1,4):
            m,C0,r=build(poly,8,nz,.24,30,field)
            panels,C=ports(m,C0,r,21,canonical=True)
            gs.append([panel_capture(m['xyz'],f,C[:,21*i:21*(i+1)],p)[0]
                for i,(f,p) in enumerate(zip(m['apertureFaces'],panels))])
        np.testing.assert_allclose(gs[0],gs[1],atol=1e-12)
if __name__=='__main__':unittest.main()

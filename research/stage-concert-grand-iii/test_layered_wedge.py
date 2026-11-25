import unittest
import numpy as np
from inclined_lid import build
from lid_exterior import ports
from acoustic_trace_resolution import panel_capture,describe
from hybrid_cavity import build as hybrid,response
class LayeredWedgeTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.2,.7],[.7,1.5],[0.,1.]])
        self.field=lambda xy:np.c_[np.ones(len(xy)),xy[:,0]]
    def test_geometry_and_default(self):
        m0,C0,r0=build(self.poly,6,2,.24,55,self.field)
        m1,C1,r1=build(self.poly,6,2,.24,55,self.field,wedge_layers=1)
        np.testing.assert_array_equal(m0['xyz'],m1['xyz']);np.testing.assert_array_equal(m0['tet'],m1['tet'])
        np.testing.assert_array_equal(C0,C1)
        for k in (2,4,8):
            m,C,r=build(self.poly,6,2,.24,55,self.field,wedge_layers=k)
            self.assertEqual(r['wedgeLayers'],k)
            self.assertAlmostEqual(r['wedgeVolumeM3'],r0['wedgeVolumeM3'],places=12)
            np.testing.assert_allclose(r['portAreasM2'],r0['portAreasM2'],atol=1e-12)
            np.testing.assert_allclose(C.sum(0),1.,atol=1e-12)
            for a,b in zip(m['aperturePolygons'],m0['aperturePolygons']):np.testing.assert_array_equal(a,b)
            self.assertGreater(len(m['tet']),len(m0['tet']))
        with self.assertRaises(ValueError):build(self.poly,6,2,.24,55,self.field,wedge_layers=0)
    def test_trace_recovery(self):
        mins=[];nulls=[]
        for k in (1,8):
            m,C0,r=build(self.poly,14,1,.24,30,self.field,wedge_layers=k)
            pp,C=ports(m,C0,r,21,canonical=True)
            rr=[describe(panel_capture(m['xyz'],f,C[:,21*i:21*(i+1)],p)[0])
                for i,(f,p) in enumerate(zip(m['apertureFaces'],pp))]
            mins.append(min(x['minimumCapturedEnergy'] for x in rr))
            nulls.append(sum(x['nearNullModes'] for x in rr))
        self.assertGreater(nulls[0],0);self.assertEqual(nulls[1],0)
        self.assertGreater(mins[1],mins[0]+.1)
    def test_hybrid_response(self):
        m=hybrid(self.poly,7,2,.24,30,self.field,6,wedge_layers=3)
        Z,P,r=response(m,80.,[[.3,.5,.12]])
        self.assertTrue(r['gate']);self.assertEqual(m['report']['wedgeLayers'],3)
        self.assertEqual(Z.shape[0],2+6*len(m['panels']))
if __name__=='__main__':unittest.main()

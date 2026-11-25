import unittest,json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from board_contour import hull
from spline_plate import assemble
from trace_plate import restrict
from rim_structure import beam,assemble as rim_assemble,response
from ribbed_plate import response as plate_response
from bridge_board_interface import plate as rectangle
ROOT=Path(__file__).parent
class TraceRimTest(unittest.TestCase):
    def setUp(self):
        self.poly=hull([[0,0],[1,0],[1,1.2],[0,1.2]])
        self.p=json.loads((ROOT/'board_interface_hypothesis.json').read_text())['plate']
        self.r=json.loads((ROOT/'ribbed_plate_hypothesis.json').read_text())['rib']
        self.cfg=json.loads((ROOT/'rim_structure_hypothesis.json').read_text())
    def test_trace(self):
        m=restrict(assemble(self.poly,[],self.p,self.r,6,12,False))
        f,_=plate_response(m,[[.5,.6]],[100],self.p,False)
        M,K,_=rectangle({'x':[0,1],'y':[0,1.2]},self.p,8)
        self.assertLess(abs(f[0]/min(np.sqrt(K/M)/(2*np.pi))-1),.01)
        self.assertEqual(m['rank'],m['fullRank']);self.assertLess(m['independentTraceResidual'],1e-8)
    def test_oblique(self):
        p=hull([[0,0],[1,0],[1,.4],[.8,1.2],[0,1.2]])
        m=restrict(assemble(p,[],self.p,self.r,9,14,False))
        self.assertGreater(m['constrainedRank'],8)
        self.assertGreater(min(eigh(m['K'],m['M'],eigvals_only=True)),0)
    def test_closed_rim(self):
        M,K,F,mass=beam(self.poly,3,660,1e10,.04,.08,2e6)
        v=np.zeros(len(M));v[::2]=1
        self.assertAlmostEqual(float(v@M@v),mass,places=12)
        self.assertLess(abs(float(v@K@v)),1e-6)
        self.assertAlmostEqual(float(v@F@v),2e6*4.4,places=5)
    def test_reciprocal_joint(self):
        m=assemble(self.poly,[],self.p,self.r,4,12,False)
        a=rim_assemble(m,self.cfg,2,8);z=rim_assemble(m,self.cfg,2,8,False)
        x=np.sin(np.arange(len(a['M'])))*1e-5;v=np.cos(np.arange(len(x)))*1e-3
        expected=sum(self.cfg['joint']['stiffnessNperM2']*float(w@((R@x)*(R@v))) for R,w in a['maps'])
        self.assertAlmostEqual(float(v@a['J']@x),expected,places=11)
        y,_,_=response(m,a,[[.5,.5]],[100,150]);u,_,_=response(m,z,[[.5,.5]],[100,150])
        self.assertGreater(np.max(abs(y[:,0,1])),1e-10);self.assertLess(np.max(abs(u[:,0,1])),1e-14)
if __name__=='__main__':unittest.main()

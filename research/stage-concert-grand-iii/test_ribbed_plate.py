import unittest,json
from pathlib import Path
import numpy as np
from ribbed_plate import quadrature,Basis,assemble,response
from board_contour import hull
from bridge_board_interface import plate as rectangle
ROOT=Path(__file__).parent
class RibTest(unittest.TestCase):
    def setUp(self):
        self.poly=hull([[0,0],[1,0],[1,1.2],[0,1.2]])
        self.p=json.loads((ROOT/'board_interface_hypothesis.json').read_text())['plate']
        self.r=json.loads((ROOT/'ribbed_plate_hypothesis.json').read_text())['rib']
    def test_quadrature(self):
        x,w=quadrature(self.poly,8);self.assertAlmostEqual(sum(w),1.2)
        self.assertAlmostEqual(float(w@x[:,0]),.6)
    def test_boundary(self):
        b=Basis(self.poly,4);S,*_=b.evaluate([[0,.3],[1,.7],[.4,0],[.6,1.2]])
        self.assertLess(np.max(abs(S)),1e-13)
        q=np.array([[.4,.5]]);h=1e-4;S,X,C,Y=b.evaluate(q)
        np.testing.assert_allclose(X,(b.evaluate(q+[h,0])[0]-2*S+b.evaluate(q-[h,0])[0])/h**2,rtol=1e-5,atol=1e-5)
    def test_rectangle(self):
        m=assemble(self.poly,[],self.p,self.r,8,20);f,_=response(m,[[.5,.6]],[100],self.p,False)
        M,K,_=rectangle({'x':[0,1],'y':[0,1.2]},self.p,8)
        self.assertLess(abs(f[0]/min(np.sqrt(K/M)/(2*np.pi))-1),.01)
    def test_ribs(self):
        ribs=[dict(startXYZ_m=[.5,.1,0],endXYZ_m=[.5,1.1,0])]
        m=assemble(self.poly,ribs,self.p,self.r,6,20)
        self.assertAlmostEqual(m['ribMassKg'],self.r['densityKgM3']*self.r['widthM']*self.r['heightM'])
        self.assertGreater(np.linalg.norm(m['Mr']),0.);self.assertGreater(np.linalg.norm(m['Kr']),0.)
        f,y=response(m,[[.3,.4],[.7,.8]],[80,100,150],self.p,True)
        self.assertGreater(f[0],0.);self.assertGreater(np.max(abs(y[:,0,1])),0.)
if __name__=='__main__':unittest.main()

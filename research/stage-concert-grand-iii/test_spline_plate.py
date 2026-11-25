import unittest,json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from board_contour import hull
from ribbed_plate import response
from bridge_board_interface import plate as rectangle
from spline_plate import LocalBasis,assemble,rim_matrices
ROOT=Path(__file__).parent
class SplineTest(unittest.TestCase):
    def setUp(self):
        self.poly=hull([[0,0],[1,0],[1,1.2],[0,1.2]])
        self.p=json.loads((ROOT/'board_interface_hypothesis.json').read_text())['plate']
        self.r=json.loads((ROOT/'ribbed_plate_hypothesis.json').read_text())['rib']
    def test_partition(self):
        b=LocalBasis(self.poly,4,False);S,X,C,Y=b.evaluate([[.31,.22],[.9,.8]])
        np.testing.assert_allclose(S.sum(1),1.,atol=1e-12)
        for q in (X,C,Y):np.testing.assert_allclose(q.sum(1),0.,atol=1e-11)
    def test_rectangle(self):
        m=assemble(self.poly,[],self.p,self.r,5,12);f,_=response(m,[[.5,.6]],[100],self.p,False)
        M,K,_=rectangle({'x':[0,1],'y':[0,1.2]},self.p,8)
        self.assertLess(abs(f[0]/min(np.sqrt(K/M)/(2*np.pi))-1),.01)
        self.assertAlmostEqual(m['areaM2'],1.2,places=11);self.assertEqual(m['rank'],m['fullRank'])
    def test_polygon(self):
        poly=hull([[0,0],[1,0],[1,.4],[.7,1.2],[0,.9]])
        m=assemble(poly,[],self.p,self.r,5,14)
        self.assertEqual(m['rank'],m['fullRank'])
        S=m['basis'].evaluate((poly+np.roll(poly,-1,axis=0))/2)[0]
        self.assertLess(np.max(abs(S)),1e-12)
        self.assertGreater(min(eigh(m['K'],m['M'],eigvals_only=True)),0.)
    def test_rim(self):
        m=assemble(self.poly,[],self.p,self.r,3,12,False)
        z,r=rim_matrices(m,2e6,200.,12)
        v=np.linalg.lstsq(m['T'],np.ones(m['T'].shape[0]),rcond=None)[0]
        self.assertAlmostEqual(float(v@z@v),2e6*4.4,places=4)
        self.assertLess(abs(float(v@r@v)),1e-7)
        self.assertLess(abs(float(v@m['K']@v)),1e-6)
        a=eigh(m['K']+z+r,m['M'],eigvals_only=True);b=eigh(m['K']+2*z+2*r,m['M'],eigvals_only=True)
        self.assertGreater(min(a),0.);self.assertTrue(np.all(b>=a-1e-5))
if __name__=='__main__':unittest.main()

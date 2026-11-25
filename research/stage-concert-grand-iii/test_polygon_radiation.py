import unittest,json
from pathlib import Path
import numpy as np
from board_contour import hull
from spline_plate import assemble
from polygon_radiation import modes,SurfaceModes,response
ROOT=Path(__file__).parent
class PolygonTest(unittest.TestCase):
    def test_modes(self):
        M=np.diag([2.,3.,4.]);K=np.diag([1e4,9e4,1e16]);D=.1*M;P=np.eye(3)
        q=modes(M,K,D,P,2)
        np.testing.assert_allclose(np.diag(q['K']),[5000.,30000.],rtol=1e-12)
        self.assertLess(q['massError'],1e-12);self.assertLess(q['scaledEigenResidual'],1e-12)
    def test_surface(self):
        p=hull([[0,0],[1,0],[1,.4],[.7,1.2],[0,.9]])
        mat=json.loads((ROOT/'board_interface_hypothesis.json').read_text())['plate']
        rib=json.loads((ROOT/'ribbed_plate_hypothesis.json').read_text())['rib']
        m=assemble(p,[],mat,rib,4,12,False);U=np.random.default_rng(2).normal(size=(len(m['M']),3))
        x=np.array([[0.,0.],[.5,.5],[.3,.7],[.7,1.2]])
        np.testing.assert_allclose(SurfaceModes(m,U)(x),m['basis'].evaluate(x)[0]@m['T']@U,rtol=1e-10,atol=1e-10)
    def test_power(self):
        q=dict(M=np.eye(2),K=np.diag([1e5,2e5]),D=np.eye(2),P=np.eye(2))
        Z=np.array([[2+3j,.3+.2j],[.3+.2j,1+2j]])
        Y,p,s=response(q,Z,np.eye(2),80)
        self.assertLess(s['powerRelative'],1e-12);self.assertLess(s['reciprocity'],1e-12)
        self.assertGreater(s['airPowerFraction'],0.);self.assertLess(s['airPowerFraction'],1.)
if __name__=='__main__':unittest.main()

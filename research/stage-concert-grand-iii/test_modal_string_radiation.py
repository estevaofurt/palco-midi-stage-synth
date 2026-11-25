import unittest,os,json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from string_structure import Wire,full_reference
from modal_string_radiation import response
class ModalStringRadiationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(Path(os.environ['G3_SCALE_REPORT']).read_text())['rows']
    def test_full_reference(self):
        M=np.diag([.02,.03]);K=np.array([[2e6,-1e6],[-1e6,2e6]]);D=np.diag([3.,5.]);P=np.zeros((2,4));P[:,2:]=np.eye(2)
        wires=[Wire(self.rows[24],32,0,0,'a'),Wire(self.rows[24],32,0,0,'b'),Wire(self.rows[27],32,1,1,'c')]
        w2,U=eigh(K,M);q=dict(M=np.eye(2),K=np.diag(w2),D=U.T@D@U,P=U.T@P)
        Z=np.array([[2.+1j,.2+.1j],[.2+.1j,1.+2j]]);H=np.array([[1.+2j,3.],[2.,1.-1j]])
        A,B,C,F=full_reference(M,K,D,P,wires)
        for f in (30,65,110,130,150):
            y,o,s=response(q,[U[w.rear] for w in wires],wires,U.T@Z@U,H@U,f)
            omega=2*np.pi*f;dynamic=B-omega**2*A+1j*omega*C;dynamic[:2,:2]+=1j*omega*Z
            v=1j*omega*np.linalg.solve(dynamic,F)
            np.testing.assert_allclose(y,F.T@v,rtol=1e-8,atol=1e-12)
            np.testing.assert_allclose(o,H@v[:2],rtol=1e-8,atol=1e-12);self.assertTrue(s['gate'])
    def test_no_air(self):
        q=dict(M=np.eye(2),K=np.diag([1e5,2e5]),D=np.eye(2),P=np.eye(2))
        y,o,s=response(q,[],[],np.zeros((2,2)),np.zeros((2,2)),50.)
        self.assertTrue(s['gate']);self.assertEqual(s['lossFractions']['air'],0.);self.assertEqual(s['lossFractions']['strings'],0.)
    def test_active_load_rejected(self):
        q=dict(M=np.eye(2),K=np.eye(2),D=np.eye(2),P=np.eye(2))
        with self.assertRaises(AssertionError):response(q,[],[],-np.eye(2),np.eye(2),50.)
if __name__=='__main__':unittest.main()

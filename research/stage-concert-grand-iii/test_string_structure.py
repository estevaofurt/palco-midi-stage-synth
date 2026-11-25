import unittest,json,os
from pathlib import Path
import numpy as np
from string_structure import Wire,response,full_reference
from structural_response import response as full_response
class StringStructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(Path(os.environ['G3_SCALE_REPORT']).read_text())['rows']
    def test_exact_condensation(self):
        M=np.diag([.02,.03]);K=np.array([[2e6,-1e6],[-1e6,2e6]]);D=np.diag([3.,5.])
        P=np.zeros((2,4));P[:,2:]=np.eye(2)
        wires=[Wire(self.rows[45-21],32,0,0,'a'),Wire(self.rows[45-21],32,0,0,'b'),Wire(self.rows[48-21],32,1,1,'c')]
        f=[30,65,110,130,150]
        y,s,_=response(M,K,D,P,wires,f)
        A,B,C,F=full_reference(M,K,D,P,wires)
        z,t,_=full_response(A,B,C,F,f,np.ones(4))
        self.assertTrue(s['gate'] and t['gate'])
        np.testing.assert_allclose(y,z,rtol=1e-7,atol=1e-11)
        self.assertGreater(np.max(abs(y[:,0,1])),1e-10)
    def test_no_cross_when_separated(self):
        M=np.diag([.02,.03]);K=np.diag([2e6,2e6]);D=np.diag([3.,5.])
        P=np.zeros((2,2));wires=[Wire(self.rows[45-21],32,0,0,'a'),Wire(self.rows[48-21],32,1,1,'b')]
        y,s,_=response(M,K,D,P,wires,[30,65,110,130,150])
        self.assertTrue(s['gate']);self.assertLess(np.max(abs(y[:,0,1])),1e-14)
    def test_unison_mass_once(self):
        M=np.array([[.02]]);K=np.array([[2e6]]);D=np.array([[3.]]);P=np.zeros((1,1))
        w=Wire(self.rows[45-21],32,0,0,'a');v=Wire(self.rows[45-21],32,0,0,'b')
        A,B,C,F=full_reference(M,K,D,P,[w,v])
        self.assertAlmostEqual(A[0,0],M[0,0]+w.M[0,0]+v.M[0,0],places=14)
        self.assertAlmostEqual(F[0,0],w.P[0]+v.P[0],places=14)
if __name__=='__main__':unittest.main()

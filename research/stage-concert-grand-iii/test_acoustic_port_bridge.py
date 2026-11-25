import unittest
import numpy as np
from lid_exterior import Panel
from common_exterior import board_panel,eliminate
from acoustic_port_bridge import bridge,reference_couple
class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        self.field=lambda x:np.c_[np.ones(len(x)),x[:,0]]
        self.board=board_panel(self.poly,self.field)
        a=np.c_[self.poly,np.ones(4)];b=a+np.array([0.,0.,1.])
        n=np.array([0.,0.,1.])
        self.cavity=[Panel(a,n,3),Panel(b,n,3)]
        self.ext=[Panel(np.roll(b,1,axis=0),n,3),Panel(np.roll(a,2,axis=0),n,3),self.board]
    def test_permutation_and_congruence(self):
        E,r=bridge(self.cavity,self.ext,self.board)
        self.assertEqual(r['aperturePermutation'],[1,0])
        rng=np.random.default_rng(12);A=rng.normal(size=(8,8));Z=A.T@A+np.eye(8)+1j*np.eye(8)
        C=2j*np.eye(8);Pc=rng.normal(size=(2,8));Pe=rng.normal(size=(3,8))
        total,pi,pe,U,Q,rep=reference_couple(C,Pc,E@Z@E.T,Pe@E.T,E,2,reference_kind='common-free-space-monopole')
        z,p,u,q,rr=eliminate(C,Pc,Z,2)
        np.testing.assert_allclose(total,z,atol=1e-10);np.testing.assert_allclose(pi,p,atol=1e-10)
        np.testing.assert_allclose(pe,Pe@q,atol=1e-10);np.testing.assert_allclose(U,u,atol=1e-10)
        self.assertTrue(rep['gate']);self.assertFalse(rep['radiationReady'])
    def test_reject_unapproved_and_wrong_geometry(self):
        E,_=bridge(self.cavity,self.ext,self.board)
        with self.assertRaises(ValueError):reference_couple(1j*np.eye(8),np.ones((1,8)),np.eye(8),np.ones((1,8)),E,2,reference_kind='experimental-bem')
        with self.assertRaises(ValueError):bridge(self.cavity,[self.ext[0],self.ext[0],self.board],self.board)
        with self.assertRaises(ValueError):bridge(self.cavity,[self.ext[0],self.ext[1],board_panel(self.poly,lambda x:np.c_[np.ones(len(x)),x[:,1]])],self.board)
if __name__=='__main__':unittest.main()

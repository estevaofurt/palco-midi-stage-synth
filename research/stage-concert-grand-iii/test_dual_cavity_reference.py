import unittest
import numpy as np
from dual_cavity_reference import couple
from common_exterior import herm
class DualCavityTest(unittest.TestCase):
    def test_independent_identical_cavities(self):
        Z=np.array([[3j,1j],[1j,2j]]);Pe=np.eye(2);P=np.eye(2);Ze=4*np.eye(2)
        total,pu,pl,pe,F,r=couple(Z,P,Z,P,Ze,Pe,1,reference_kind='common-free-space-monopole')
        np.testing.assert_allclose(F[:,0],[1j/(4+2j),-1j/(4+2j)])
        np.testing.assert_allclose(total,[[2*(3j+1/(4+2j))]])
        np.testing.assert_allclose(pu,-pl);self.assertTrue(r['gate'])
        self.assertFalse(r['radiationReady'])
    def test_cross_radiation(self):
        rng=np.random.default_rng(32);nb=2;na=3;nl=4
        def matrix(n):
            A=rng.normal(size=(n,n));B=rng.normal(size=(n,n))
            return A.T@A+np.eye(n)+1j*(B+B.T)
        Zu,Zl,Ze=matrix(nb+na),matrix(nb+nl),matrix(na+nl)
        Pu,Pl,Pe=np.eye(nb+na),np.eye(nb+nl),np.eye(na+nl)
        total,pu,pl,pe,F,r=couple(Zu,Pu,Zl,Pl,Ze,Pe,nb,reference_kind='common-free-space-monopole')
        np.testing.assert_allclose((Zu@pu)[nb:],(Ze@F)[:na],atol=1e-10)
        np.testing.assert_allclose((Zl@pl)[nb:],(Ze@F)[na:],atol=1e-10)
        np.testing.assert_allclose(pu[:nb],np.eye(nb));np.testing.assert_allclose(pl[:nb],-np.eye(nb))
        expected=pu.conj().T@herm(Zu)@pu+pl.conj().T@herm(Zl)@pl+F.conj().T@herm(Ze)@F
        np.testing.assert_allclose(herm(total),expected,atol=1e-10)
        self.assertTrue(r['gate'])
        with self.assertRaises(ValueError):couple(Zu,Pu,Zl,Pl,Ze,Pe,nb,reference_kind='experimental-bem')
        bad=Ze.copy();bad[0,1]+=1
        with self.assertRaises(ValueError):couple(Zu,Pu,Zl,Pl,bad,Pe,nb,reference_kind='common-free-space-monopole')
if __name__=='__main__':unittest.main()

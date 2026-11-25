import unittest
import numpy as np
from common_exterior import board_panel,eliminate
from hybrid_cavity import terminate
from lid_exterior import Panel,load,pressure
from split_radiation import relative
class CommonExteriorTest(unittest.TestCase):
    def test_independent_limit(self):
        Zc=1j*np.array([[4.,1.],[1.,3.]])
        Ze=np.diag([2+1j,3+2j]);P=np.array([[1.,.4]])
        z,p,u,q,r=eliminate(Zc,P,Ze,1)
        y,pr,U,rep=terminate(Zc,P,Ze[:1,:1],1)
        self.assertTrue(r['gate'] and rep['gate'])
        np.testing.assert_allclose(z,y+Ze[1:,1:])
        np.testing.assert_allclose(p,pr)
        np.testing.assert_allclose(u,U)
        self.assertAlmostEqual(r['crossPowerTrace'],0.)
    def test_cross_power_and_active_guard(self):
        Zc=1j*np.array([[4.,1.],[1.,3.]])
        Ze=np.array([[2+1j,1+.4j],[1+.4j,3+2j]])
        z,p,u,q,r=eliminate(Zc,np.eye(2),Ze,1)
        self.assertTrue(r['gate'],r)
        self.assertNotEqual(r['crossPowerTrace'],0.)
        np.testing.assert_allclose((z+z.conj().T)/2,q.conj().T@((Ze+Ze.conj().T)/2)@q)
        with self.assertRaises(ValueError):eliminate(Zc,np.eye(2),-np.eye(2),1)
    def test_common_free_space_monopole_limit(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        board=board_panel(poly,lambda x:np.ones((len(x),1)))
        top=Panel(np.c_[poly,np.full(4,.5)],np.array([0.,0.,1.]),1)
        f=.01;Z,r=load([top,board],[f],10,18,16)[0]
        self.assertTrue(r['gate'],r)
        np.testing.assert_allclose(Z.real/Z[0,0].real,np.ones((2,2)),atol=1e-6)
        # Equal and opposite volume velocities interfere destructively at low k.
        q=np.array([[1.],[-1.]])
        self.assertLess(float((q.T@Z.real@q)[0,0]/Z[0,0].real),1e-6)
        self.assertTrue(np.isfinite(pressure([top,board],q,[[2.,2.,2.]],f,10)).all())
if __name__=='__main__':unittest.main()

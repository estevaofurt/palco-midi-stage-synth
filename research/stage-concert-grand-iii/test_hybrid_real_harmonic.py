import unittest
import numpy as np
from hybrid_real_harmonic import real_vertical
from hybrid_cavity import vertical,build,response
from split_radiation import relative
class RealHarmonicTest(unittest.TestCase):
    def test_analytic_continuation(self):
        c=343.;h=.24;omega=2*np.pi*250;k2=(omega/c)**2
        lam=np.array([0.,k2*.5,k2*(1-1e-15),k2,k2*(1+1e-15),k2*2,1e8])
        _,_,s,d,r=vertical(lam,h,1j*omega,c)
        ss,dd,rr=real_vertical(lam,h,omega,c)
        for x,y in zip((s,d,r),(ss,dd,rr)):
            np.testing.assert_allclose(x,y,rtol=1e-10,atol=1e-10)
            self.assertFalse(np.iscomplexobj(y))
        with self.assertRaises(ValueError):real_vertical(np.array([0.]),h,c*np.pi/(2*h),c)
        with self.assertRaises(ValueError):real_vertical(np.array([1.+0j]),h,omega,c)
    def test_layered_equivalence(self):
        poly=np.array([[0.,0.],[1.,0.],[1.2,.7],[.7,1.5],[0.,1.]])
        field=lambda x:np.c_[np.ones(len(x)),x[:,0]]
        for angle in (30,55):
            m=build(poly,10,1,.24,angle,field,10,wedge_layers=4,boundary_n=20)
            for f in (30.,80.,150.,250.,300.):
                Z,P,r=response(m,f,[[.3,.5,.12]],solver='schur')
                z,p,rr=response(m,f,[[.3,.5,.12]],solver='schur-real')
                self.assertTrue(r['gate'] and rr['gate'])
                self.assertLess(relative(Z,z),1e-9);self.assertLess(relative(P,p),1e-9)
                self.assertEqual(rr['linearSolve']['interfaceDenseMatrixBytes']*2,r['linearSolve']['interfaceDenseMatrixBytes'])
            with self.assertRaises(ValueError):response(dict(m,C=m['C'].astype(complex)),80.,[[.3,.5,.12]],solver='schur-real')
if __name__=='__main__':unittest.main()

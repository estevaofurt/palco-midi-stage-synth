import unittest
import numpy as np
from prism_cavity import build,response,tail_sum
from closed_cavity import assemble,response as tet_response
from split_radiation import relative

class PrismTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.,.8],[0.,.8]])
        self.h=.24
        self.points=np.array([[.3,.4,.06],[.7,.6,.18]])
    def test_uniform_exact_solution(self):
        m=build(self.poly,5,self.h,lambda x:np.ones((len(x),1)))
        for s in (20+2j*np.pi*150,2j*np.pi*300):
            Z,P,r=response(m,s,self.points,12)
            lam=s/m['c']
            exact=m['rho']*s*m['area']/lam/np.tanh(lam*self.h)
            ep=m['rho']*s*np.cosh(lam*(self.h-self.points[:,2]))/(lam*np.sinh(lam*self.h))
            self.assertTrue(r['gate'],r)
            self.assertLess(abs(Z[0,0]-exact)/abs(exact),1e-4)
            self.assertLess(relative(P[:,0],ep),1e-4)
    def test_tail_and_tetrahedral_reference(self):
        field=lambda x:np.c_[np.ones(len(x)),x[:,0]]
        m=build(self.poly,12,self.h,field)
        s=2j*np.pi*80
        a,b,r=response(m,s,self.points,12)
        x,y,q=response(m,s,self.points,24)
        self.assertTrue(r['gate'] and q['gate'])
        self.assertLess(max(relative(a,x),relative(b,y)),1e-3)
        t=assemble(self.poly,12,8,self.h,field)
        z,p,r=tet_response(t,s,self.points)
        self.assertTrue(r['gate'])
        self.assertLess(max(relative(x,z),relative(y,p)),.05)
        self.assertAlmostEqual(tail_sum(self.h,0.,0),self.h/3)
if __name__=='__main__':unittest.main()

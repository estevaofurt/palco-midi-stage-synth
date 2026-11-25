import unittest
import numpy as np
from hybrid_cavity import build,response,terminate,vertical
from closed_cavity import response as tetra
from lid_exterior import load
from split_radiation import relative
class HybridTest(unittest.TestCase):
    def test_vertical_limits(self):
        a,d,sech,dt,ratio=vertical(np.array([0.,1e8]),.24,0j,343.)
        self.assertAlmostEqual(ratio[0].real,.24)
        self.assertAlmostEqual(sech[0].real,1.)
        self.assertTrue(np.isfinite(ratio).all())
        self.assertAlmostEqual(dt[1].real,1e4)
    def test_wedge_and_termination(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,.8],[0.,.8]])
        field=lambda x:np.c_[np.ones(len(x)),x[:,0]]
        m=build(poly,12,8,.24,30,field,3)
        points=np.array([[.3,.4,.06],[.7,.6,.18]])
        f=80.;Z,P,r=response(m,f,points)
        self.assertTrue(r['gate'],r)
        full=dict(m['full'],B=np.column_stack([m['full']['B'],m['Cfull']]))
        z,p,q=tetra(full,2j*np.pi*f,points);self.assertTrue(q['gate'])
        self.assertLess(max(relative(Z,z),relative(P,p)),.05)
        ze,rep=load(m['panels'],[f],12,22,20)[0]
        y,p,u,r=terminate(Z,P,ze,2)
        self.assertTrue(r['gate'],r)
if __name__=='__main__':unittest.main()

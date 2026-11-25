import unittest
import numpy as np
from lid_exterior import Panel
from nested_acoustic_ports import embedding,project
from lower_prism import build,response
from split_radiation import relative
class ExtendedFluxTest(unittest.TestCase):
    def test_skew_geometry_and_embeddings(self):
        a=np.array([[0.,0.,0.],[2.,.01,0.],[1.8,.031,0.]])
        normal=np.array([0.,0.,1.]);high=Panel(a,normal,36)
        for n in (1,3,6,10,15,21,28,36):
            low=Panel(np.roll(a,1,axis=0),normal,n);T,r=embedding([high],[low])
            self.assertTrue(r['gate'])
            self.assertEqual(T.shape,(36,n))
        _,x,w,V=high.samples(16)
        np.testing.assert_allclose(high.basis.area*V.T@(w[:,None]*V),np.eye(36),atol=1e-9)
        np.testing.assert_allclose(w@V,np.r_[1.,np.zeros(35)],atol=1e-10)
    def test_lower_trace_and_response_projection(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,.7],[0.,1.]])
        field=lambda x:np.column_stack([np.ones(len(x)),x[:,0]])
        hi=build(poly,10,.18,field,36);lo=build(poly,10,.18,field,21)
        T,_=embedding([hi['mouth']],[lo['mouth']])
        from scipy.linalg import block_diag
        E=block_diag(np.eye(2),T)
        self.assertLess(relative(hi['B']@E,lo['B']),1e-9)
        p=[[.5,.3,-.09]];s=2j*np.pi*80
        Z,P,r=response(hi,s,p);z,pp,rr=response(lo,s,p)
        Y,Q=project(Z,P,E)
        self.assertLess(relative(Y,z),1e-9);self.assertLess(relative(Q,pp),1e-9)
        self.assertTrue(r['gate'] and rr['gate'])
if __name__=='__main__':unittest.main()

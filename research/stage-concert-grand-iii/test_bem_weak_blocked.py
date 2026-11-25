import unittest
import numpy as np
from test_exterior_bem import sphere
from bem_p1_static_moments import fit as reference,operators
from bem_weak_p1_refined import quadrature
from exterior_bem import elements
from bem_weak_blocked import assemble,fit
from split_radiation import relative

class BlockedWeakTest(unittest.TestCase):
    def test_raw_assembly(self):
        t=sphere(.5,0);N=len(t);k=2*np.pi*80/343.
        v=lambda x,o:np.c_[np.ones(len(x)),x[:,0],x[:,2]]
        x,w,L=quadrature(t,4);_,n,a=elements(t)
        D=np.zeros((N,3,3*N),complex);B=np.zeros((N,3,3))
        for j in range(len(L)):
            _,K=operators(t,x[:,j],n,np.arange(N),k,5,True)
            W=w[:,j,None]*L[j][None,:]
            D+=W[:,:,None]*K[:,None,:]
            B+=W[:,:,None]*v(x[:,j],np.arange(N))[:,None,:]
        for block in (1,7,32,256):
            d,b,s=assemble(t,k,4,5,v,block=block)
            self.assertLess(relative(d,D.reshape(3*N,3*N)),1e-12)
            self.assertLess(relative(b,B.reshape(3*N,3)),1e-12)
            np.testing.assert_array_equal(s,np.repeat(np.sqrt(a),3))
    def test_solution_equivalence(self):
        t=sphere(.5,1);v=lambda x,o:np.c_[np.ones(len(x)),x[:,0]]
        for f in (30.,150.):
            k=2*np.pi*f/343.;q,r=reference(t,k,3,4,v)
            z,s=fit(t,k,3,4,v,block=16)
            self.assertLess(relative(z,q),1e-10)
            self.assertLess(s['weakResidual'],1e-8)
            self.assertLess(s['blockedContributionBytes'],s['legacyContributionBytes'])
        with self.assertRaises(ValueError):fit(t,k,3,4,v,block=0)
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from exterior_bem import samples,self_potential,operators as ordinary,elements
from bem_static_split import laplace,operators,fit,audit
from test_exterior_bem import sphere
from split_radiation import relative
class StaticSplitTest(unittest.TestCase):
    def test_triangle_analytic(self):
        t=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]])
        x=np.array([[.2,.3,.7],[.8,.6,-.3]])
        S,G=laplace(t,x);y,w=samples(t,48)
        d=x[:,None,None,:]-y[None,:,:,:];r=np.linalg.norm(d,axis=-1)
        s=np.sum(w[None,:,:]/(4*np.pi*r),axis=-1)
        g=-np.sum(w[None,:,:,None]*d/(4*np.pi*r[:,:,:,None]**3),axis=2)
        np.testing.assert_allclose(S,s,rtol=1e-10,atol=1e-12)
        np.testing.assert_allclose(G,g,rtol=1e-10,atol=1e-12)
        xx=np.array([[.2,.3,0.]])
        s,g=laplace(t,xx,np.array([0]))
        np.testing.assert_allclose(s[:,0],self_potential(xx,t,0,64).real,rtol=1e-9)
        s,g=laplace(t,np.array([[.2,.3,1e-8],[.2,.3,-1e-8]]))
        np.testing.assert_allclose(g[:,0,2],[-.5,.5],atol=1e-7)
    def test_dynamic_against_independent(self):
        t=sphere(.5,1);x,n,_=elements(t);owner=np.arange(len(t));k=2*np.pi*150/343.
        G,D=operators(t,x,n,owner,k,6)
        g,d=ordinary(t,x,n,owner,k,24)
        self.assertLess(relative(G,g),1e-4)
        self.assertLess(relative(D,d),1e-4)
    def test_sphere_smoke(self):
        t=sphere(.5,2);k=2*np.pi*80/343.;q,r=fit(t,np.ones((len(t),1)),k,5)
        z,p,rep=audit(t,q,np.ones((3*len(t),1)),k,[[1.,0.,0.]],7)
        exact=4*np.pi*.5**2*1j*1.204*343*k/(2+1j*k)
        self.assertLess(abs(z[0,0]-exact)/abs(exact),.15)
        self.assertLess(rep['powerRelative'],.15)
if __name__=='__main__':unittest.main()

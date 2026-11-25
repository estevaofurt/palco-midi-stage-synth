import unittest
import numpy as np
from exterior_bem import elements,subdivide,topology,fit,audit,heldout,self_potential
from bem_envelope import triangulate,velocities
from neumann_envelope import envelope,geometry_audit

def sphere(a,level):
    e=np.eye(3);tris=[]
    for i in (-1,1):
        for j in (-1,1):
            for k in (-1,1):
                t=np.array([i*e[0],j*e[1],k*e[2]])*a
                if i*j*k<0:t=t[[0,2,1]]
                tris.append(t)
    t=np.array(tris)
    for _ in range(level):t=subdivide(t,lambda x:a*x/np.linalg.norm(x,axis=1)[:,None])
    return t
class BemTest(unittest.TestCase):
    def test_self_integral_and_mesh(self):
        t=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]])
        x=t.mean(1)
        z=self_potential(x,t,0,24)
        zz=self_potential(2*x,2*t,0,24)
        np.testing.assert_allclose(zz,2*z,atol=1e-12)
        self.assertGreater(z.real[0],0.)
    def test_envelope(self):
        poly=np.array([[0.,0.],[1.,-.5],[1.,.5]])
        s,p,c=envelope(poly,.24,30,3,lambda x:np.ones((len(x),1)))
        for level in (0,1):
            t,labels,r=triangulate(s,level)
            self.assertTrue(r['gate'])
            self.assertAlmostEqual(r['volume'],geometry_audit(s,p,c)['volume'],places=10)
            x,n,a=elements(t);V=velocities(s,p,x,labels)
            np.testing.assert_allclose(a@V,np.r_[np.tile([1.,0.,0.],len(p)-1),.5],atol=1e-9)
    def test_sphere_radiation(self):
        a=.5;k=2*np.pi*80/343.;rho=1.204;c=343.
        t=sphere(a,2);self.assertTrue(topology(t)['gate'])
        q,r=fit(t,np.ones((len(t),1)),k,6)
        self.assertLess(r['collocationResidual'],1e-10)
        x,n,w,owner=heldout(t)
        Z,P,rep=audit(t,q,np.ones((len(x),1)),k,[[1.,0.,0.]],8)
        exact=4*np.pi*a*a*1j*rho*c*k/(1/a+1j*k)
        # Coarse faceted sphere smoke test; exact spherical geometry is not used.
        self.assertLess(abs(Z[0,0]-exact)/abs(exact),.15)
        self.assertGreater(Z.real[0,0],0.)
        self.assertLess(rep['powerRelative'],.15)
if __name__=='__main__':unittest.main()

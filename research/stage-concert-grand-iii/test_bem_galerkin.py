import unittest
import numpy as np
from test_exterior_bem import sphere
from exterior_bem import elements
from bem_galerkin import assembly,project,fit,weak_impedance,static_audit
from bem_static_split import fit as collocate
from bem_adaptive import independent
from bem_linear import CHECK,targets
from split_radiation import relative
class GalerkinTest(unittest.TestCase):
    def test_static_flux_and_projection(self):
        t=sphere(.5,1);x,n,a=elements(t)
        B=project(t,lambda x:np.c_[np.ones(len(x)),x[:,0]],4)
        np.testing.assert_allclose(B[:,0],a,atol=1e-12)
        np.testing.assert_allclose(B[:,1],a*x[:,0],atol=1e-12)
        r=static_audit(t,8,6)
        self.assertLess(r['staticFluxBalance'],.005,r)
        self.assertLess(r['singleLayerReciprocity'],.005,r)
        self.assertGreater(r['minimumSingleLayerEigenvalue'],0.)
    def test_sphere(self):
        t=sphere(.5,1);k=2*np.pi*80/343.;_,_,a=elements(t)
        S,D,r=assembly(t,k,5,5);B=a[:,None];q,rep=fit(S,D,B)
        self.assertLess(rep['weakResidual'],1e-10)
        z=weak_impedance(S,B,q,a,k)
        x,n,w,own=targets(t,CHECK)
        Z,P,rr=independent(t,q,np.ones((len(x),1)),k,[[1.,0.,0.]],7)
        exact=4*np.pi*.5**2*1j*1.204*343*k/(2+1j*k)
        self.assertLess(abs(Z[0,0]-exact)/abs(exact),.25)
        self.assertLess(relative(z,Z),.02)
        self.assertLess(rr['powerRelative'],.15)
if __name__=='__main__':unittest.main()

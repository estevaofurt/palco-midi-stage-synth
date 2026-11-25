import unittest
import numpy as np
from bem_linear import COL,CHECK,shape,targets,projected_shapes,operators,fit,audit
from bem_static_split import operators as constant
from test_exterior_bem import sphere
from split_radiation import relative
class LinearBemTest(unittest.TestCase):
    def test_shape_and_constant_reproduction(self):
        np.testing.assert_allclose(shape(COL),np.eye(3),atol=1e-15)
        t=sphere(.5,1);x,n,w,owner=targets(t,CHECK)
        np.testing.assert_allclose(projected_shapes(t,x)[np.arange(len(x)),owner],np.tile(shape(CHECK),(len(t),1)),atol=1e-12)
        k=2*np.pi*150/343.
        G,D=operators(t,x,n,owner,k,6);g,d=constant(t,x,n,owner,k,6)
        self.assertLess(relative(G.reshape(len(x),len(t),3).sum(-1),g),1e-5)
        self.assertLess(relative(D.reshape(len(x),len(t),3).sum(-1),d),1e-10)
    def test_linear_sphere(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        q,r=fit(t,np.ones((3*len(t),1)),k,6)
        self.assertLess(r['collocationResidual'],1e-10)
        Z,P,rr=audit(t,q,np.ones((6*len(t),1)),k,[[1.,0.,0.]],8)
        exact=4*np.pi*.5**2*1j*1.204*343*k/(2+1j*k)
        self.assertLess(abs(Z[0,0]-exact)/abs(exact),.25)
        self.assertLess(rr['powerRelative'],.15)
if __name__=='__main__':unittest.main()

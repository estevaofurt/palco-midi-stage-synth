import unittest
import numpy as np
from test_exterior_bem import sphere
from bem_linear import COL,targets,operators,fit as dense_fit
from bem_oversampled import audit as dense_audit,audit_targets
from bem_p1_stream import derivative,fit,audit,trace
class StreamTest(unittest.TestCase):
    def test_operator_and_trace(self):
        t=sphere(.5,1);x,n,w,o=audit_targets(t)
        rng=np.random.default_rng(12);q=rng.normal(size=(3*len(t),2))+1j*rng.normal(size=(3*len(t),2))
        for k in (0.,2*np.pi*150/343.):
            G,D=operators(t,x,n,o,k,5)
            np.testing.assert_allclose(derivative(t,x,n,o,k,5),D,rtol=1e-12,atol=1e-12)
            for batch in (7,24):
                P,U=trace(t,q,x,n,o,k,5,batch)
                np.testing.assert_allclose(P,G@q,rtol=1e-11,atol=1e-12)
                np.testing.assert_allclose(U,-D@q,rtol=1e-11,atol=1e-12)
    def test_fit_and_audit(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        x,n,w,o=targets(t,COL);V=np.c_[np.ones(len(x)),x[:,0]]
        q,_=fit(t,V,k,5);q0,_=dense_fit(t,V,k,5,derivative_only=False)
        np.testing.assert_allclose(q,q0,rtol=1e-11,atol=1e-12)
        x,n,w,o=audit_targets(t);V=np.c_[np.ones(len(x)),x[:,0]]
        Z,P,r=audit(t,q,V,k,[[1.,0.,0.]],6,batch=17)
        z,p,s=dense_audit(t,q0,V,k,[[1.,0.,0.]],6)
        np.testing.assert_allclose(Z,z,rtol=1e-11,atol=1e-12)
        np.testing.assert_allclose(P,p,rtol=1e-11,atol=1e-12)
        for name in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative','passivityMinRelative'):
            self.assertAlmostEqual(r[name],s[name],places=11)
        self.assertEqual(r['gate'],s['gate'])
        self.assertLess(r['streamTraceMatrixBytes'],r['denseTraceMatrixBytes'])
if __name__=='__main__':unittest.main()

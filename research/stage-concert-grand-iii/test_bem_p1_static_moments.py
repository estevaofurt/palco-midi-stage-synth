import unittest
import numpy as np
from bem_p1_static_moments import static,operators,fit,audit
from bem_static_split import laplace,operators as p0
from bem_linear import rule,shape,targets,COL
from exterior_bem import samples
from test_exterior_bem import sphere
from bem_oversampled import audit_targets
class StaticMomentTest(unittest.TestCase):
    def test_moments_independent(self):
        t=np.array([[[0.,0.,0.],[1.,0.,0.],[.2,.7,0.]]])
        x=np.array([[.3,.2,.4],[.3,-.05,.08]])
        G,dG=static(t,x);y,w=samples(t,100);u,v,_=rule(100);S=shape(np.c_[1-u,u*(1-v),u*v])
        d=x[:,None,None,:]-y[None,:,:,:];rad=np.linalg.norm(d,axis=-1)
        ref=np.einsum('btq,qa->bta',w[None,:,:]/(4*np.pi*rad),S)
        dr=np.einsum('btqd,qa->btad',-d*w[None,:,:,None]/(4*np.pi*rad[:,:,:,None]**3),S)
        np.testing.assert_allclose(G,ref,rtol=1e-8,atol=1e-10)
        np.testing.assert_allclose(dG,dr,rtol=1e-7,atol=1e-9)
        for a in range(3):
            h=np.eye(3)[a]*1e-6
            fd=(static(t,x+h)[0]-static(t,x-h)[0])/(2e-6)
            np.testing.assert_allclose(dG[:,:,:,a],fd,rtol=1e-6,atol=1e-9)
    def test_constant_and_jump(self):
        t=sphere(.5,1);x,n,w,o=targets(t,COL)
        S,g=static(t,x,o);s,d=laplace(t,x,o)
        np.testing.assert_allclose(S.sum(2),s,atol=1e-12)
        np.testing.assert_allclose(g.sum(2),d,atol=1e-12)
        for k in (0.,2*np.pi*80/343.):
            G,D=operators(t,x,n,o,k,6);g,d=p0(t,x,n,o,k,6)
            np.testing.assert_allclose(G.reshape(len(x),len(t),3).sum(2),g,atol=1e-11)
            np.testing.assert_allclose(D.reshape(len(x),len(t),3).sum(2),d,atol=1e-9)
    def test_sphere(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        v=lambda x,o:np.ones((len(x),1))
        q,r=fit(t,k,4,6,v);self.assertLess(r['weakResidual'],1e-10)
        x,n,w,o=audit_targets(t);Z,P,rr=audit(t,q,v(x,o),k,[[1.,0.,0.]],7)
        exact=4*np.pi*.5**2*1j*1.204*343*k/(2+1j*k)
        self.assertLess(abs(Z[0,0]-exact)/abs(exact),.25)
        self.assertLess(rr['powerRelative'],.15)
    def test_mesh_guard(self):
        from bem_mesh_guard import signature,require_same_mesh
        t=sphere(.5,1);labels=np.arange(len(t));s=signature(t,labels)
        self.assertTrue(require_same_mesh(s,signature(t.copy(),labels.copy())))
        with self.assertRaises(ValueError):require_same_mesh(s,signature(t[::-1],labels[::-1]))
        with self.assertRaises(ValueError):require_same_mesh(s,signature(t,labels+1))
        modified=t.copy();modified[0,0,0]+=1e-9
        with self.assertRaises(ValueError):require_same_mesh(s,signature(modified,labels))
if __name__=='__main__':unittest.main()

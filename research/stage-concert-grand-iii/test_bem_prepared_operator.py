import unittest
import numpy as np
from exterior_bem import elements
from bem_weak_p1_refined import quadrature
from bem_p1_static_moments import operators
from bem_prepared_operator import PreparedOperator
from bem_weak_blocked import assemble,fit
from bem_power_partition import integrate
from split_radiation import relative
def fixture():
    x=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
    return x[np.array([[0,2,1],[0,1,3],[0,3,2],[1,2,3]])]
def velocity(x,o):return np.column_stack([np.ones(len(x)),x[:,0],x[:,1]])
class PreparedTest(unittest.TestCase):
    def test_operator_equivalence(self):
        t=fixture();x,w,L=quadrature(t,4);_,n,_=elements(t);o=np.arange(len(t));p=PreparedOperator(t,6)
        for k in (.55,2.7):
            for deriv in (False,True):
                a,b=operators(t,x[:,0],n,o,k,6,deriv);c,d=p(t,x[:,0],n,o,k,6,deriv)
                np.testing.assert_array_equal(b,d)
                if deriv:self.assertIsNone(c)
                else:np.testing.assert_array_equal(a,c)
        with self.assertRaises(ValueError):p(t+.1,x[:,0],n,o,.55,6)
        with self.assertRaises(ValueError):p(t,x[:,0],n,o,.55,8)
    def test_assembly_and_work(self):
        t=fixture();a=assemble(t,1.5,3,5,velocity,block=2);b=assemble(t,1.5,3,5,velocity,block=2,reuse_sources=True)
        for u,v in zip(a,b):np.testing.assert_array_equal(u,v)
        q,r=fit(t,1.5,3,5,velocity,block=2,reuse_sources=True)
        p=PreparedOperator(t,5)
        P,C,r=integrate(t,q,velocity,1.5,3,5,operator=operators)
        S,T,s=integrate(t,q,velocity,1.5,3,5,operator=p)
        self.assertLess(relative(P,S),1e-12);self.assertLess(relative(C,T),1e-12)
        self.assertEqual(r,s)
if __name__=='__main__':unittest.main()

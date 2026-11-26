import unittest
import numpy as np
from felt_law import Felt
from multi_hammer_contact import solve_contacts,probe
class MultiTest(unittest.TestCase):
    def test_signed_cross_compliance(self):
        f=Felt(1.5e8,.5e8,3000.,3.,2.5);d=np.array([.001,.0015]);z=np.zeros(2)
        G=np.array([[2e-5,-1e-5],[-1e-5,2e-5]])
        a,_,_=solve_contacts(np.zeros(2),d,z,G,[f,f])
        b,_,_=solve_contacts(np.zeros(2),d,z,G,[f,f],True)
        np.testing.assert_allclose(a,b,rtol=1e-9,atol=1e-10)
        self.assertTrue(np.all(a>0))
    def test_no_contact(self):
        f=Felt(1.5e8,.5e8,3000.,3.,2.5)
        a,_,_=solve_contacts(np.zeros(2),-np.ones(2),np.eye(2),np.zeros(2),[f,f])
        np.testing.assert_array_equal(a,np.zeros(2))
    def test_reference(self):
        self.assertTrue(probe(2,4,48000)['gate'])
if __name__=='__main__':unittest.main()

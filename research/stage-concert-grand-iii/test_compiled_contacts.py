import unittest
import numpy as np
from compiled_contacts import ContactSolver,fixture,probe
class ContactTest(unittest.TestCase):
    def test_cases(self):
        for k in ('weak','positive','signed'):self.assertTrue(probe(8,k)['gate'])
    def test_invalid(self):
        G,f,*_=fixture(2,'weak')
        with self.assertRaises(ValueError):ContactSolver(-G,f)
    def test_no_contact(self):
        G,f,*_=fixture(2,'signed');a=ContactSolver(G,f)
        F,s,e=a.solve(np.zeros(2),-np.ones(2),np.zeros(2))
        np.testing.assert_array_equal(F,np.zeros(2))
    def test_nonconvergence(self):
        G,f,d0,df,z,*_=fixture(8,'signed');a=ContactSolver(G,f)
        with self.assertRaises(ValueError):a.solve(d0,df,z,max_sweeps=1)
if __name__=='__main__':unittest.main()

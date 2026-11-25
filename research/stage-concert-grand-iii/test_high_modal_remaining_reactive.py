import unittest
import numpy as np
from lid_exterior import Panel
from high_modal_remaining_reactive import classify,compare_self,compare_pair,FREQ
class RemainingTest(unittest.TestCase):
    def test_classification(self):
        x=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]])
        n=np.array([0.,0.,1.]);p=[Panel(x,n,3),Panel(x+[1,0,0],n,3),Panel(x+[0,0,1],n,3)]
        self.assertEqual(classify(p),[(0,0,'self'),(0,1,'contact'),(0,2,'disjoint'),(1,1,'self'),(1,2,'disjoint'),(2,2,'self')])
    def test_raw_asymmetry_not_hidden(self):
        x=np.tile(np.eye(3),(len(FREQ),1,1));y=x.copy();y[:,0,1]=.005
        self.assertTrue(compare_self([x,x,x],x)['gate'])
        self.assertFalse(compare_self([x,y,y],x)['gate'])
        self.assertTrue(compare_pair([x,x,x],x)['gate'])
        self.assertFalse(compare_pair([x,x,x*1.1],x)['gate'])
if __name__=='__main__':unittest.main()

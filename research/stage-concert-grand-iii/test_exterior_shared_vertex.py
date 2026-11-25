import unittest
import numpy as np
from lid_exterior import Panel
from exterior_shared_vertex import contacts,vertex_duffy,vertex_delta
from exterior_shared_edge import tensor_triangle
from exterior_pair_stream import pair_integrals
from split_radiation import relative
class VertexTest(unittest.TestCase):
    def fixture(self,count):
        a=np.array([[0.,0.,0.],[1.,0.,0.],[.5,.7,0.]])
        b=np.array([[0.,0.,0.],[-1.,0.,0.],[-.5,0.,.8]])
        return Panel(a,np.array([0.,0.,1.]),count),Panel(b,np.array([0.,1.,0.]),count)
    def test_contact_and_reciprocity(self):
        p,q=self.fixture(6);rows=contacts(p,q)
        self.assertEqual(len(rows),4);self.assertTrue(all(n==1 for i,j,n,ids in rows))
        i,j,_,_=rows[0];k=np.array([.55,2.7])
        R,X,r=vertex_duffy(p,q,i,j,k,16)
        S,Y,_=vertex_duffy(q,p,j,i,k,16)
        self.assertAlmostEqual(r['areaProduct'],r['expectedAreaProduct'],places=12)
        self.assertLess(relative(R,S.transpose(0,2,1)),1e-10)
        self.assertLess(relative(X,Y.transpose(0,2,1)),1e-10)
        _,fine,_=vertex_duffy(p,q,i,j,k,22)
        self.assertLess(relative(X,fine),1e-3)
    def test_high_degree_and_edge_exclusion(self):
        p,q=self.fixture(55);k=np.array([.55,5.5])
        delta,r=vertex_delta(p,q,k,24,24)
        self.assertEqual(r['vertexPairs'],4);self.assertLess(r['smoothControlMaximum'],1e-8)
        self.assertTrue(np.isfinite(delta).all())
        x=np.array([[0.,0.,0.],[1.,0.,0.],[.5,0.,.8]])
        q=Panel(x,np.array([0.,-1.,0.]),6)
        rows=contacts(p,q)
        self.assertEqual(sum(n==2 for _,_,n,_ in rows),1)
        self.assertGreater(sum(n==1 for _,_,n,_ in rows),0)
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from lid_exterior import Panel
from shared_vertex_modal_replay import inventory,require_sources
class VertexReplayTest(unittest.TestCase):
    def test_inventory(self):
        x=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]])
        n=np.array([0.,0.,1.]);p=[Panel(x,n,3),Panel(x+[1,0,0],n,3),Panel(x+[2,1,0],n,3)]
        r=inventory(p)
        self.assertEqual([(v['panel'],v['otherPanel'],v['edgePairs']) for v in r],[(0,1,1),(1,2,0)])
        self.assertEqual(r[1]['vertexPairs'],4)
    def test_guard(self):
        with self.assertRaises(ValueError):require_sources({}, {},30,'a'*64,[])
if __name__=='__main__':unittest.main()

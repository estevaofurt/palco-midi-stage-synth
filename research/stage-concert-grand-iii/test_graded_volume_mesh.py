import unittest
import numpy as np
from graded_volume_mesh import build,audit
from inclined_lid import build as original
class GradedVolumeTest(unittest.TestCase):
    def test_geometry(self):
        poly=np.array([[0.,0.],[1.,0.],[1.2,.7],[.7,1.5],[0.,1.]])
        for angle in (30,55):
            old=build(poly,8,16,4,.24,angle,0.,0.)
            m,_,r=original(poly,8,1,.24,angle,lambda x:np.ones((len(x),1)),wedge_layers=4,boundary_n=16)
            np.testing.assert_allclose(old['xyz'],m['xyz'],atol=1e-13)
            np.testing.assert_array_equal(np.array(sorted(map(tuple,np.sort(old['tet'],axis=1)))),np.array(sorted(map(tuple,np.sort(m['tet'],axis=1)))))
            new=build(poly,8,16,4,.24,angle,.5,.5);a=audit(new,poly,16,4,.24,angle,.5,.5)
            self.assertTrue(a['gate']);self.assertEqual(a['apertureFaces'],r['faces'])
if __name__=='__main__':unittest.main()

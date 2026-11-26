import unittest
import numpy as np
from hammer_lifecycle import HammerBank,probe
class LifecycleTest(unittest.TestCase):
    def test_idle(self):
        a=HammerBank(2,4,48000);F,r=a.step()
        np.testing.assert_array_equal(F,np.zeros(2));self.assertEqual(a.idle_steps,1);self.assertEqual(a.storage(),0.)
    def test_launch_energy(self):
        a=HammerBank(2,4,48000);a.z[0]=1e-4
        E=a.storage();a.launch(0,1.)
        self.assertAlmostEqual(a.storage()-E,.005,places=13)
        self.assertEqual(a.z[0],1e-4)
        with self.assertRaises(ValueError):a.launch(0,1.)
    def test_repetition(self):
        self.assertTrue(probe(2,4,48000)['gate'])
if __name__=='__main__':unittest.main()

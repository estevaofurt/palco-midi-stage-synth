import unittest
from baffle_frequency_grid import check_split,TRAIN,VALID,PREVIOUS,FREQ
class GridTest(unittest.TestCase):
    def test_split(self):
        check_split()
        self.assertEqual((len(TRAIN),len(VALID),len(FREQ)),(12,6,18))
        self.assertTrue(set(PREVIOUS)<=set(TRAIN))
        self.assertFalse(set(TRAIN)&set(VALID))
if __name__=='__main__':unittest.main()

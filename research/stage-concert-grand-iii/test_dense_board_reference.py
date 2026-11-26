import unittest
from dense_frequency_batch import BATCHES,FREQ,NEW,grid_check
from dense_board_reference import require_batch
from fixed_355_validation import METRICS
class DenseTest(unittest.TestCase):
    def test_grid(self):
        self.assertEqual(len(grid_check()),21)
        self.assertEqual(len(set(BATCHES[0])|set(BATCHES[1])),12)
        self.assertFalse(set(FREQ+list(NEW))&set(BATCHES[0]+BATCHES[1]))
    def test_incomplete(self):
        with self.assertRaises(ValueError):require_batch({},30.,'x',0,'y')
if __name__=='__main__':unittest.main()

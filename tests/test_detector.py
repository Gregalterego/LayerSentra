import unittest
import numpy as np
from printwatch.detector import decode

class DecodeTests(unittest.TestCase):
    def test_same_class_duplicates_removed_other_class_preserved(self):
        rows=np.array([[320,320,200,200,.9,.1,.1,.1],
                       [320,320,200,200,.8,.1,.1,.1],
                       [320,320,200,200,.1,.85,.1,.1]])
        result=decode(rows.T[None],640,640,(640,640,0,0))
        self.assertEqual([d['category'] for d in result],['spaghetti','blob'])
    def test_letterbox_coordinates_return_to_original_frame(self):
        rows=np.array([[320,320,320,160,.9,.1,.1,.1]])
        result=decode(rows[None],640,640,(640,320,0,160))
        self.assertTrue(np.allclose(result[0]['box'],[.25,.25,.5,.5]))
    def test_normalized_output(self):
        rows=np.array([[.5,.5,.5,.5,.9,.1,.1,.1]])
        result=decode(rows[None],640,640,(640,640,0,0))
        self.assertTrue(np.allclose(result[0]['box'],[.25,.25,.5,.5]))
    def test_wrong_class_count_fails(self):
        with self.assertRaises(ValueError): decode(np.zeros((1,9,100)),640,640,(640,640,0,0))

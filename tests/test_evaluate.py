import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from layerscan.config import DEFAULT
from layerscan.evaluate import evaluate

class EvaluationTests(unittest.TestCase):
    @patch('layerscan.evaluate.Detector')
    def test_duplicate_prediction_is_false_positive_and_missing_truth_is_false_negative(self,model):
        d={'category':'spaghetti','score':.9,'box':[.1,.1,.2,.2]}
        model.return_value.infer.return_value=([d,dict(d)],10)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); Image.new('RGB',(32,32)).save(root/'frame.png')
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps([{'image':'frame.png','annotations':[
                {'category':'spaghetti','box':[.1,.1,.2,.2]},
                {'category':'blob','box':[.6,.6,.2,.2]}]}]))
            report=evaluate(manifest,copy.deepcopy(DEFAULT))
        self.assertEqual(report['categories']['spaghetti']['tp'],1)
        self.assertEqual(report['categories']['spaghetti']['fp'],1)
        self.assertEqual(report['categories']['spaghetti']['precision'],.5)
        self.assertEqual(report['categories']['blob']['fn'],1)

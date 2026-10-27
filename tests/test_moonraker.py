import unittest
from unittest.mock import patch,Mock
from layersentra.io import Moonraker

class MoonrakerTests(unittest.TestCase):
    @patch('layersentra.io.requests.post')
    def test_http_error_never_marks_pause_confirmed(self,post):
        client=Moonraker('http://printer')
        client.status=Mock(return_value={'state':'printing'})
        post.return_value.raise_for_status.side_effect=RuntimeError('HTTP 500')
        with self.assertRaises(RuntimeError): client.pause()
    @patch('layersentra.io.requests.post')
    def test_successful_request_requires_observed_pause(self,post):
        client=Moonraker('http://printer'); client.status=Mock(side_effect=[{'state':'printing'},{'state':'paused'}])
        post.return_value.json.return_value={'result':'ok'}
        self.assertTrue(client.pause())
    @patch('layersentra.io.requests.post')
    def test_completed_print_cannot_be_paused(self,post):
        client=Moonraker('http://printer'); client.status=Mock(return_value={'state':'complete'})
        with self.assertRaises(RuntimeError): client.pause()
        post.assert_not_called()

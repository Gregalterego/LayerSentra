import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from layersentra.app import app, OBSERVATION_TOKEN, PTZ_TOKEN, TOKEN, monitor
from layersentra.ptz import PTZ, DIRECTIONS

class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
        self.mobile=patch('layersentra.app.MOBILE',{'hostname':'watch.example.org','login':'owner@example.org'})
        self.mobile.start();self.addCleanup(self.mobile.stop)
        self.headers={'Tailscale-User-Login':'owner@example.org','X-LayerSentra-Token':OBSERVATION_TOKEN}
    def test_remote_can_toggle_observation_but_cannot_choose_pause(self):
        for enabled in (True,False):
            with patch.object(monitor,'configure') as configure:
                r=self.client.post('/api/observation',base_url='https://watch.example.org',json={'enabled':enabled},headers=self.headers)
                self.assertEqual(r.status_code,200)
                self.assertEqual(configure.call_args.args[0]['action'],'observe')
                self.assertEqual(configure.call_args.args[0]['monitoring'],enabled)
        with patch.object(monitor,'configure') as configure:
            r=self.client.post('/api/observation',base_url='https://watch.example.org',json={'enabled':True,'action':'pause'},headers=self.headers)
            self.assertEqual(r.status_code,400);configure.assert_not_called()
    def test_wrong_token_identity_origin_and_type_rejected(self):
        for headers,payload in (({**self.headers,'X-LayerSentra-Token':TOKEN},{'enabled':True}),
            ({**self.headers,'Origin':'https://evil.example'},{'enabled':True}),
            ({**self.headers,'Tailscale-User-Login':'other@example.org'},{'enabled':True}),
            (self.headers,{'enabled':'true'})):
            with patch.object(monitor,'configure') as configure:
                r=self.client.post('/api/observation',base_url='https://watch.example.org',json=payload,headers=headers)
                self.assertIn(r.status_code,(400,403));configure.assert_not_called()
    def test_ptz_has_a_separate_scope(self):
        with patch('layersentra.app.ptz.move') as move:
            r=self.client.post('/api/ptz',base_url='https://watch.example.org',json={'direction':'left'},headers=self.headers)
            self.assertEqual(r.status_code,403);move.assert_not_called()
            r=self.client.post('/api/ptz',base_url='https://watch.example.org',json={'direction':'left'},headers={**self.headers,'X-LayerSentra-Token':PTZ_TOKEN})
            self.assertEqual(r.status_code,200);move.assert_called_once_with('left')

class PTZTests(unittest.TestCase):
    def test_not_configured_never_sends(self):
        with tempfile.TemporaryDirectory() as folder, patch('layersentra.ptz.requests.post') as post:
            ptz=PTZ(Path(folder)/'ptz.json')
            self.assertFalse(ptz.availability()['enabled'])
            with self.assertRaises(ValueError):ptz.move('left')
            post.assert_not_called()
    def test_bounded_command_and_no_redirects(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ptz.json'
            cfg={'enabled':True,'camera_id':'secondary','bridge_auto_stop':True,
                 'commands':{d:'http://127.0.0.1:7140/'+d for d in DIRECTIONS}}
            path.write_text(json.dumps(cfg));ptz=PTZ(path)
            with patch('layersentra.ptz.requests.post',return_value=Mock(status_code=204)) as post:
                ptz.move('left')
                self.assertEqual(post.call_args.kwargs['json'],{'duration_ms':200})
                self.assertFalse(post.call_args.kwargs['allow_redirects'])
                with self.assertRaises(ValueError):ptz.move('http://evil.example')
                self.assertEqual(post.call_count,1)
            cfg['bridge_auto_stop']=False;path.write_text(json.dumps(cfg))
            self.assertFalse(ptz.availability()['enabled'])

    def test_malformed_local_settings_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ptz.json'
            for content in ('[]','null','{"enabled": true, "commands": []}'):
                path.write_text(content)
                self.assertFalse(PTZ(path).availability()['enabled'])

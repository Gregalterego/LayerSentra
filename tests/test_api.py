import unittest
from unittest.mock import patch
from layersentra.app import app,TOKEN

class ApiTests(unittest.TestCase):
    def setUp(self): self.client=app.test_client()
    def test_external_host_refused(self):
        self.assertEqual(self.client.get('/api/status',base_url='http://printer.example').status_code,403)
    def test_cross_origin_cannot_change_config(self):
        r=self.client.post('/api/config',base_url='http://localhost:7127',json={},headers={'Origin':'http://other.example','X-LayerSentra-Token':TOKEN})
        self.assertEqual(r.status_code,403)
    def test_missing_token_refused(self):
        self.assertEqual(self.client.post('/api/config',base_url='http://localhost:7127',json={}).status_code,403)
    def test_invalid_configuration_is_not_written(self):
        with patch('layersentra.app.save') as save:
            r=self.client.post('/api/config',base_url='http://localhost:7127',json={'action':'cancel'},headers={'X-LayerSentra-Token':TOKEN})
            self.assertEqual(r.status_code,400); save.assert_not_called()
    def test_startup_observation_only(self):
        r=self.client.get('/api/config',base_url='http://localhost:7127')
        self.assertEqual(r.json['config']['action'],'observe')
        self.assertFalse(r.json['config']['monitoring'])

class MobileTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
        self.mobile=patch('layersentra.app.MOBILE',{'hostname':'mac.test.ts.net','login':'owner@example.test'})
        self.mobile.start(); self.addCleanup(self.mobile.stop)
    def test_mobile_without_identity_refused(self):
        self.assertEqual(self.client.get('/api/status',base_url='https://mac.test.ts.net').status_code,403)
    def test_mobile_other_user_refused(self):
        self.assertEqual(self.client.get('/api/status',base_url='https://mac.test.ts.net',headers={'Tailscale-User-Login':'other@example.test'}).status_code,403)
    def test_owner_gets_no_control_token_or_camera_url(self):
        r=self.client.get('/api/config',base_url='https://mac.test.ts.net',headers={'Tailscale-User-Login':'owner@example.test'})
        self.assertEqual(r.status_code,200); self.assertTrue(r.json['read_only'])
        self.assertIsNone(r.json['token']); self.assertEqual(r.json['config']['cameras'][0]['url'],'')
    def test_mobile_cannot_change_configuration_even_with_token(self):
        r=self.client.post('/api/config',base_url='https://mac.test.ts.net',json={},headers={'Tailscale-User-Login':'owner@example.test','X-LayerSentra-Token':TOKEN})
        self.assertEqual(r.status_code,403)
    def test_direct_remote_request_cannot_spoof_proxy(self):
        r=self.client.get('/api/status',base_url='https://mac.test.ts.net',headers={'Tailscale-User-Login':'owner@example.test'},environ_overrides={'REMOTE_ADDR':'100.64.0.2'})
        self.assertEqual(r.status_code,403)

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from layersentra.guest import create_app, digest

class GuestTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'guest.json'
        self.cfg = dict(origin='https://guest.example.org', camera_id='secondary', enabled=True,
                        expires_at=time.time()+3600, token_hash=digest('secret-invite'),
                        session_key='x'*64)
        self.write()
        self.app = create_app(self.path)
        self.app.testing = True
        self.client = self.app.test_client()
        self.base = 'https://guest.example.org'
        self.headers = {'Origin': self.base}

    def write(self):
        self.path.write_text(json.dumps(self.cfg))

    def post(self, path, body, headers=None):
        return self.client.post(path, base_url=self.base, json=body, headers=headers or self.headers)

    def login(self):
        self.assertEqual(self.post('/session', {'token':'secret-invite'}).status_code, 200)
        with self.client.session_transaction(base_url=self.base) as session:
            self.headers['X-Guest-CSRF'] = session['csrf']

    def test_anonymous_cannot_read_or_act(self):
        with patch('layersentra.guest.requests.get') as get, patch('layersentra.guest.Moonraker') as moon:
            for path in ('/api/status', '/api/frame'):
                self.assertEqual(self.client.get(path, base_url=self.base).status_code,401)
            self.assertEqual(self.post('/api/pause',{}).status_code,401)
            get.assert_not_called(); moon.assert_not_called()

    def test_only_allowed_paths_even_after_login(self):
        self.login()
        with patch('layersentra.guest.requests.post') as post:
            for path in ('/api/config','/api/observation','/printer/gcode/script',
                         '/printer/print/resume','/printer/print/cancel','/static/index.html','/api/frame/primary'):
                self.assertEqual(self.post(path,{}).status_code,403)
            post.assert_not_called()

    def test_revoke_rotate_expire_invalidate_active_sessions(self):
        self.login()
        for cfg in ({'enabled':False}, {'expires_at':time.time()-1}, {'token_hash':digest('rotated')}):
            previous=self.cfg.copy();self.cfg.update(cfg);self.write()
            self.assertIn(self.post('/api/pause',{}).status_code,(401,403))
            self.cfg=previous;self.write()

    def test_origin_csrf_and_host_required(self):
        self.login()
        with patch('layersentra.guest.Moonraker') as moon:
            for headers in ({'Origin':self.base}, {**self.headers,'Origin':'https://evil.example'},
                            {k:v for k,v in self.headers.items() if k!='Origin'}):
                self.assertEqual(self.post('/api/pause',{},headers).status_code,403)
            self.assertEqual(self.client.get('/api/status',base_url='https://evil.example').status_code,403)
            moon.assert_not_called()

    def test_pause_only_fixed_action_and_confirmed(self):
        self.login()
        with patch('layersentra.guest.Moonraker') as moon, patch('layersentra.guest.load',return_value={'moonraker_url':'http://local.invalid'}):
            for body in ({'command':'RESUME'}, {'url':'http://evil.invalid'}, None, []):
                self.assertIn(self.post('/api/pause',body).status_code,(400,403))
            moon.assert_not_called()
            moon.return_value.status.return_value={'state':'printing'}
            response=self.post('/api/pause',{})
            self.assertEqual(response.status_code,200)
            moon.return_value.pause.assert_called_once_with()
            self.assertEqual(response.json['state'],'paused')
            self.assertEqual(self.post('/api/pause',{}).status_code,429)

    def test_pause_failure_never_claims_success(self):
        self.login()
        with patch('layersentra.guest.Moonraker') as moon, patch('layersentra.guest.load',return_value={'moonraker_url':'http://local.invalid'}):
            moon.return_value.status.return_value={'state':'printing'}
            moon.return_value.pause.side_effect=RuntimeError('private address')
            response=self.post('/api/pause',{})
            self.assertEqual(response.status_code,502)
            self.assertNotIn('private address',response.get_data(as_text=True))

    def test_ptz_disabled_without_verified_camera_scope(self):
        self.login()
        with patch('layersentra.guest.requests.get') as get, patch('layersentra.guest.requests.post') as post:
            get.return_value=Mock(status_code=200)
            get.return_value.json.return_value={'ptz_token':'private','capabilities':{'ptz':{'enabled':True,'camera_id':'primary'}}}
            self.assertEqual(self.post('/api/ptz',{'direction':'left'}).status_code,409)
            post.assert_not_called()

    def test_ptz_fixed_direction_private_token_and_no_redirect(self):
        self.login()
        with patch('layersentra.guest.requests.get') as get, patch('layersentra.guest.requests.post') as post:
            get.return_value=Mock(status_code=200)
            get.return_value.json.return_value={'ptz_token':'private','capabilities':{'ptz':{'enabled':True,'camera_id':'secondary'}}}
            post.return_value=Mock(status_code=200)
            self.assertEqual(self.post('/api/ptz',{'direction':'left','duration_ms':10000}).status_code,400)
            self.assertEqual(self.post('/api/ptz',{'direction':'left'}).status_code,200)
            self.assertEqual(post.call_args.kwargs['json'],{'direction':'left'})
            self.assertFalse(post.call_args.kwargs['allow_redirects'])
            self.assertEqual(self.post('/api/ptz',{'direction':'right'}).status_code,429)
            self.assertEqual(self.post('/api/ptz',{'direction':'stop'}).status_code,200)

    def test_status_redacts_private_data(self):
        self.login()
        with patch('layersentra.guest.requests.get') as get:
            get.return_value=Mock(status_code=200)
            get.return_value.json.side_effect=[{'printer':{'state':'printing','filename':'private.gcode'},
                 'cameras':{'secondary':{'state':'ok','captured_at':time.time(),'url':'secret'}}},
                 {'token':'admin-secret','ptz_token':None,'capabilities':{}}]
            response=self.client.get('/api/status',base_url=self.base)
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.json['camera_ready']);self.assertFalse(response.json['ptz'])
            self.assertNotIn('private',response.get_data(as_text=True))
            self.assertNotIn('secret',response.get_data(as_text=True))

    def test_stale_frame_is_not_shown(self):
        self.login()
        with patch('layersentra.guest.requests.get') as get:
            get.return_value=Mock(status_code=200)
            get.return_value.json.return_value={'cameras':{'secondary':{'state':'ok','captured_at':time.time()-30}}}
            self.assertEqual(self.client.get('/api/frame',base_url=self.base).status_code,503)
            self.assertEqual(get.call_count,1)

    def test_cookie_and_browser_protections(self):
        response=self.post('/session',{'token':'secret-invite'})
        cookie=response.headers['Set-Cookie']
        for flag in ('Secure','HttpOnly','SameSite=Strict','Path=/'):
            self.assertIn(flag,cookie)
        self.assertEqual(response.headers['Referrer-Policy'],'no-referrer')
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(response.headers['X-Frame-Options'],'DENY')

if __name__=='__main__':unittest.main()

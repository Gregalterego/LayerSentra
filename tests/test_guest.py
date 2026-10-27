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
                        session_key='x'*64, can_resume=True)
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

    def held_action(self, action='pause', seconds=5):
        with patch('layersentra.guest.time.monotonic', return_value=100):
            token = self.post('/api/hold', {'action':action}).json['hold_token']
        with patch('layersentra.guest.time.monotonic', return_value=100+seconds):
            return self.post('/api/'+action, {'hold_token':token})

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

    def test_permanent_invite_still_has_bounded_session_and_can_be_revoked(self):
        self.cfg['expires_at'] = None
        self.write()
        self.login()
        with self.client.session_transaction(base_url=self.base) as session:
            self.assertLessEqual(session['until'], time.time() + 8 * 3600)
            self.assertGreater(session['until'], time.time() + 7 * 3600)
        self.cfg['enabled'] = False
        self.write()
        self.assertEqual(self.post('/api/pause', {}).status_code, 403)

    def test_invalid_expiry_fails_closed(self):
        for value in (True, 'never', float('inf')):
            self.cfg['expires_at'] = value
            self.write()
            self.assertEqual(self.client.get('/', base_url=self.base).status_code, 403)

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
            response=self.held_action()
            self.assertEqual(response.status_code,200)
            moon.return_value.pause.assert_called_once_with()
            self.assertEqual(response.json['state'],'paused')
            self.assertEqual(self.post('/api/pause',{}).status_code,400)

    def test_pause_failure_never_claims_success(self):
        self.login()
        with patch('layersentra.guest.Moonraker') as moon, patch('layersentra.guest.load',return_value={'moonraker_url':'http://local.invalid'}):
            moon.return_value.status.return_value={'state':'printing'}
            moon.return_value.pause.side_effect=RuntimeError('private address')
            response=self.held_action()
            self.assertEqual(response.status_code,502)
            self.assertNotIn('private address',response.get_data(as_text=True))

    def test_ptz_not_exposed_even_when_owner_supports_it(self):
        self.login()
        with patch('layersentra.guest.requests.get') as get, patch('layersentra.guest.requests.post') as post:
            self.assertEqual(self.post('/api/ptz',{'direction':'left'}).status_code,403)
            self.assertEqual(self.client.get('/api/ptz',base_url=self.base).status_code,403)
            get.assert_not_called(); post.assert_not_called()

    def test_status_redacts_private_data(self):
        self.login()
        with patch('layersentra.guest.requests.get') as get:
            get.return_value=Mock(status_code=200)
            get.return_value.json.side_effect=[{'printer':{'state':'printing','filename':'private.gcode'},
                 'cameras':{'secondary':{'state':'ok','captured_at':time.time(),'url':'secret'}}},
                 {'token':'admin-secret','ptz_token':None,'capabilities':{}}]
            response=self.client.get('/api/status',base_url=self.base)
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.json['camera_ready']);self.assertNotIn('ptz',response.json)
            self.assertNotIn('private',response.get_data(as_text=True))
            self.assertNotIn('secret',response.get_data(as_text=True))

    def test_stale_frame_is_not_shown(self):
        self.login()
        with patch('layersentra.guest.requests.get') as get:
            get.return_value=Mock(status_code=200)
            get.return_value.json.return_value={'cameras':{'secondary':{'state':'ok','captured_at':time.time()-30}}}
            self.assertEqual(self.client.get('/api/frame',base_url=self.base).status_code,503)
            self.assertEqual(get.call_count,1)

    def test_hold_minimum_duration_action_binding_expiry_and_one_use(self):
        self.login()
        with patch('layersentra.guest.Moonraker') as moon:
            for elapsed in (0,4.999,20.001):
                self.assertEqual(self.held_action(seconds=elapsed).status_code,409)
            with patch('layersentra.guest.time.monotonic',return_value=100):
                token=self.post('/api/hold',{'action':'pause'}).json['hold_token']
            with patch('layersentra.guest.time.monotonic',return_value=105):
                self.assertEqual(self.post('/api/resume',{'hold_token':token}).status_code,409)
                self.assertEqual(self.post('/api/pause',{'hold_token':token}).status_code,409)
            moon.assert_not_called()

    def test_cancelled_hold_never_sends_printer_command(self):
        self.login()
        with patch('layersentra.guest.Moonraker') as moon:
            token=self.post('/api/hold',{'action':'pause'}).json['hold_token']
            self.assertEqual(self.post('/api/hold/cancel',{'hold_token':token}).status_code,200)
            self.assertEqual(self.post('/api/pause',{'hold_token':token}).status_code,409)
            moon.assert_not_called()

    def test_resume_only_from_paused_and_once(self):
        self.login()
        with patch('layersentra.guest.Moonraker') as moon, patch('layersentra.guest.load',return_value={'moonraker_url':'http://local.invalid'}):
            moon.return_value.status.return_value={'state':'paused','fresh':True}
            result=self.held_action('resume')
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.json['state'],'printing')
            moon.return_value.resume.assert_called_once_with()
            moon.return_value.pause.assert_not_called()
            self.assertEqual(self.held_action('resume').status_code,429)

    def test_changed_printer_state_blocks_resume(self):
        self.login()
        with patch('layersentra.guest.Moonraker') as moon, patch('layersentra.guest.load',return_value={'moonraker_url':'http://local.invalid'}):
            moon.return_value.status.return_value={'state':'printing','fresh':True}
            self.assertEqual(self.held_action('resume').status_code,409)
            moon.return_value.resume.assert_not_called()

    def test_resume_error_does_not_claim_success(self):
        self.login()
        with patch('layersentra.guest.Moonraker') as moon, patch('layersentra.guest.load',return_value={'moonraker_url':'http://local.invalid'}):
            moon.return_value.status.return_value={'state':'paused','fresh':True}
            moon.return_value.resume.side_effect=RuntimeError('private-token')
            result=self.held_action('resume')
            self.assertEqual(result.status_code,502)
            self.assertNotIn('private-token',result.get_data(as_text=True))

    def test_both_cameras_exposed_only_when_explicitly_configured(self):
        self.cfg['camera_ids']=['primary','secondary'];self.write();self.login()
        with patch('layersentra.guest.requests.get') as get:
            get.return_value=Mock(status_code=200)
            get.return_value.json.return_value={'printer':{'state':'printing','fresh':True},'cameras':{
                cid:{'state':'ok','captured_at':time.time()} for cid in ('primary','secondary')}}
            result=self.client.get('/api/status',base_url=self.base)
            self.assertEqual([c['id'] for c in result.json['cameras']],['primary','secondary'])
            self.assertTrue(all(c['ready'] for c in result.json['cameras']))
            self.assertTrue(result.json['printer_ready'])
            self.assertEqual(self.client.get('/api/frame/unknown',base_url=self.base).status_code,403)

    def test_resume_requires_explicit_owner_permission(self):
        self.cfg.pop('can_resume');self.write();self.login()
        with patch('layersentra.guest.Moonraker') as moon:
            self.assertEqual(self.post('/api/hold',{'action':'resume'}).status_code,403)
            self.assertEqual(self.post('/api/resume',{}).status_code,403)
            moon.assert_not_called()

    def test_hold_cannot_be_used_from_another_session(self):
        self.login()
        token=self.post('/api/hold',{'action':'pause'}).json['hold_token']
        with self.client.session_transaction(base_url=self.base) as session:
            session['csrf']='different-session'
        self.headers['X-Guest-CSRF']='different-session'
        with patch('layersentra.guest.Moonraker') as moon:
            self.assertEqual(self.post('/api/pause',{'hold_token':token}).status_code,409)
            moon.assert_not_called()

    def test_cookie_and_browser_protections(self):
        response=self.post('/session',{'token':'secret-invite'})
        cookie=response.headers['Set-Cookie']
        for flag in ('Secure','HttpOnly','SameSite=Strict','Path=/'):
            self.assertIn(flag,cookie)
        self.assertEqual(response.headers['Referrer-Policy'],'no-referrer')
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(response.headers['X-Frame-Options'],'DENY')

if __name__=='__main__':unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from printwatch.access import proxy_identity, PROXY_HEADER
from printwatch.gateway import authorize
from printwatch.app import app, TOKEN
from printwatch.self_host_setup import prepare

HOST='watch.example.org'
SECRET='a'*48
SETTINGS={'hostname':HOST,'proxy_token':SECRET}
HASH='$2a$14$'+'a'*53

class SelfHostTests(unittest.TestCase):
    def test_only_same_machine_proxy_with_secret_and_exact_host(self):
        headers={PROXY_HEADER:SECRET}
        self.assertTrue(proxy_identity(HOST,'127.0.0.1',headers,SETTINGS))
        self.assertTrue(proxy_identity(HOST+':443','::1',headers,SETTINGS))
        for host,remote,h in ((HOST,'192.0.2.4',headers),('evil.example','127.0.0.1',headers),
                              (HOST,'127.0.0.1',{}),(HOST,'127.0.0.1',{PROXY_HEADER:'wrong'})):
            self.assertFalse(proxy_identity(host,remote,h,SETTINGS))
    def test_gateway_secret_and_origin(self):
        headers={PROXY_HEADER:SECRET,'Origin':'https://'+HOST+':8443'}
        self.assertTrue(authorize(HOST+':8443','127.0.0.1',headers,SETTINGS))
        headers['Origin']='https://evil.example'
        self.assertFalse(authorize(HOST+':8443','127.0.0.1',headers,SETTINGS))
    def test_dashboard_remains_read_only_and_hides_secrets(self):
        with patch('printwatch.app.MOBILE',SETTINGS):
            client=app.test_client();headers={PROXY_HEADER:SECRET}
            response=client.get('/api/config',base_url='https://'+HOST,headers=headers)
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.json['read_only']);self.assertIsNone(response.json['token'])
            self.assertEqual(response.json['config']['moonraker_url'],'')
            self.assertNotIn(SECRET,response.text)
            self.assertEqual(client.post('/api/config',base_url='https://'+HOST,json={},
                headers={**headers,'X-PrintWatch-Token':TOKEN}).status_code,403)
    def test_setup_writes_private_files_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            prepare(HOST,'operator',HASH,folder)
            settings=json.loads((folder/'mobile-access.json').read_text())
            self.assertGreaterEqual(len(settings['proxy_token']),32)
            text=(folder/'Caddyfile').read_text()
            self.assertEqual(text.count('basic_auth'),2)
            self.assertIn('header_up -Authorization',text)
            self.assertIn(settings['proxy_token'],text)
            self.assertEqual((folder/'mobile-access.json').stat().st_mode & 0o777,0o600)
            with self.assertRaises(FileExistsError):prepare(HOST,'operator',HASH,folder)
    def test_reject_config_injection_and_plaintext_passwords(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            for host,user,password in (('https://watch.example.org','operator',HASH),
                ('watch.example.org/path','operator',HASH),(HOST,'user\nrespond 200',HASH),
                (HOST,'operator','plaintext'),('bad..example.org','operator',HASH)):
                with self.assertRaises(ValueError):prepare(host,user,password,folder)
            self.assertEqual(list(folder.iterdir()),[])

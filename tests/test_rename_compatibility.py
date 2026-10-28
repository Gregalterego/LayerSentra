import subprocess
import sys
import unittest
from unittest.mock import patch
from layerscan.app import app, OBSERVATION_TOKEN, monitor
from layerscan.access import proxy_identity

class RenameCompatibilityTests(unittest.TestCase):
 def test_legacy_launch_command_still_resolves(self):
  result=subprocess.run([sys.executable,'-m','printwatch.app','--help'],capture_output=True,text=True,timeout=15)
  self.assertEqual(result.returncode,0,result.stderr)
  self.assertIn('--observe',result.stdout)
 def test_legacy_proxy_identity_still_works(self):
  self.assertTrue(proxy_identity('watch.example.org','127.0.0.1',
   {'X-PrintWatch-Proxy-Token':'a'*48},
   {'hostname':'watch.example.org','proxy_token':'a'*48}))
 def test_legacy_client_can_control_only_observation(self):
  with patch('layerscan.app.MOBILE',{'hostname':'watch.example.org','login':'owner@example.org'}),patch.object(monitor,'configure') as configure:
   response=app.test_client().post('/api/observation',base_url='https://watch.example.org',json={'enabled':True},
    headers={'Tailscale-User-Login':'owner@example.org','X-PrintWatch-Token':OBSERVATION_TOKEN})
   self.assertEqual(response.status_code,200)
   self.assertEqual(configure.call_args.args[0]['action'],'observe')

 def test_layersentra_launch_command_still_resolves(self):
  result=subprocess.run([sys.executable,'-m','layersentra.app','--help'],capture_output=True,text=True,timeout=15)
  self.assertEqual(result.returncode,0,result.stderr)
  self.assertIn('--observe',result.stdout)
 def test_layersentra_proxy_identity_still_works(self):
  self.assertTrue(proxy_identity('watch.example.org','127.0.0.1',
   {'X-LayerSentra-Proxy-Token':'a'*48},
   {'hostname':'watch.example.org','proxy_token':'a'*48}))
 def test_layersentra_client_can_control_observation(self):
  with patch('layerscan.app.MOBILE',{'hostname':'watch.example.org','login':'owner@example.org'}),patch.object(monitor,'configure') as configure:
   response=app.test_client().post('/api/observation',base_url='https://watch.example.org',json={'enabled':True},
    headers={'Tailscale-User-Login':'owner@example.org','X-LayerSentra-Token':OBSERVATION_TOKEN})
   self.assertEqual(response.status_code,200)
   self.assertEqual(configure.call_args.args[0]['action'],'observe')

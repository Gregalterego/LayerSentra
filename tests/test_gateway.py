import unittest
from layerscan.gateway import authorize
MOBILE={'hostname':'mac.test.ts.net','login':'owner@test'}
class GatewayTests(unittest.TestCase):
 def test_remote_without_identity_denied(self):
  self.assertFalse(authorize('mac.test.ts.net:8443','127.0.0.1',{},MOBILE))
 def test_owner_allowed(self):
  self.assertTrue(authorize('mac.test.ts.net:8443','127.0.0.1',{'Tailscale-User-Login':'owner@test','Origin':'https://mac.test.ts.net:8443'},MOBILE))
 def test_other_site_origin_denied(self):
  self.assertFalse(authorize('mac.test.ts.net:8443','127.0.0.1',{'Tailscale-User-Login':'owner@test','Origin':'https://evil.test'},MOBILE))
 def test_direct_remote_cannot_spoof(self):
  self.assertFalse(authorize('mac.test.ts.net:8443','100.64.0.1',{'Tailscale-User-Login':'owner@test'},MOBILE))
 def test_loopback_local_allowed(self):
  self.assertTrue(authorize('127.0.0.1:7128','127.0.0.1',{},MOBILE))

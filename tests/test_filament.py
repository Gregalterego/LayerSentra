import tempfile
import unittest
from pathlib import Path
from layerscan.filament import Spool, grams

CFG={'diameter_mm':1.75,'density_g_cm3':1.27,'low_warning_g':100}
class FilamentTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.s=Spool(Path(self.temp.name)/'spool.json')
 def printer(self,used,filename='a'):return {'fresh':True,'filename':filename,'filament_used_mm':used,'filament_total_mm':10000,'filament_weight_total_g':30,'filament_sensors':[{'name':'fila','enabled':False,'detected':False}]}
 def test_baseline_does_not_subtract_past_print(self):
  self.s.set_remaining(100,self.printer(5000))
  self.assertEqual(self.s.update(self.printer(5000),CFG)['spool_remaining_g'],100)
 def test_consumption_is_not_counted_twice(self):
  self.s.set_remaining(100,self.printer(5000))
  a=self.s.update(self.printer(6000),CFG)
  b=self.s.update(self.printer(6000),CFG)
  self.assertAlmostEqual(a['spool_remaining_g'],100-grams(1000,1.75,1.27))
  self.assertEqual(a['spool_remaining_g'],b['spool_remaining_g'])
 def test_new_job_counter(self):
  self.s.set_remaining(100,self.printer(5000))
  r=self.s.update(self.printer(1000,'b'),CFG)
  self.assertAlmostEqual(r['spool_remaining_g'],100-grams(1000,1.75,1.27))
  self.assertIsNotNone(r['warning'])
 def test_disabled_sensor_is_preserved_as_disabled(self):
  r=self.s.update(self.printer(1000),CFG)
  self.assertFalse(r['sensors'][0]['enabled']);self.assertIsNone(r['spool_remaining_g'])
 def test_slicer_mass_ratio_for_remaining_job(self):
  self.s.set_remaining(5,self.printer(5000))
  r=self.s.update(self.printer(5000),CFG)
  self.assertEqual(r['remaining_print_g'],15);self.assertTrue(r['spool_insufficient'])
 def test_reject_nan_baseline(self):
  with self.assertRaises(ValueError):self.s.set_remaining(float('nan'),self.printer(1000))
 def test_disconnected_does_not_consume(self):
  self.s.set_remaining(100,self.printer(5000));r=self.s.update({'fresh':False},CFG)
  self.assertEqual(r['spool_remaining_g'],100);self.assertTrue(r['stale'])
 def test_eta_needs_observed_printing_and_resets_on_pause(self):
  from unittest.mock import patch
  self.s.set_remaining(100,self.printer(1000))
  with patch('layerscan.filament.time.monotonic',side_effect=[0,30,40]):
   a=self.s.update(dict(self.printer(1000),state='printing'),CFG)
   b=self.s.update(dict(self.printer(2000),state='printing'),CFG)
   c=self.s.update(dict(self.printer(2000),state='paused'),CFG)
  self.assertIsNone(a['spool_minutes_estimate'])
  self.assertGreater(b['spool_minutes_estimate'],0)
  self.assertIsNone(c['spool_minutes_estimate'])

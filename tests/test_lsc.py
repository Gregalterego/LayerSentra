import io
import struct
import time
import unittest
from layersentra.lsc import records, LSCBridge, MAX_RECORD

class LSCTests(unittest.TestCase):
    def record(self, ts, data): return struct.pack('>4sQI', b'LSC1', ts, len(data)) + data
    def test_records_and_timestamps(self):
        data=self.record(1000,b'\0\0\0\1abc')+self.record(1100,b'xyz')
        self.assertEqual(list(records(io.BytesIO(data))),[(1000,b'\0\0\0\1abc'),(1100,b'xyz')])
    def test_truncated_header_and_payload_fail(self):
        for data in [b'LSC1',self.record(1,b'abc')[:-1],self.record(1,b'abc')[:16]]:
            with self.subTest(data=data),self.assertRaises(ValueError):list(records(io.BytesIO(data)))
    def test_invalid_magic_or_oversized_payload_fail(self):
        for magic,size in [(b'NOPE',1),(b'LSC1',MAX_RECORD+1),(b'LSC1',0)]:
            with self.assertRaises(ValueError):list(records(io.BytesIO(struct.pack('>4sQI',magic,1,size))))
    def test_stale_images_are_not_served(self):
        bridge=LSCBridge('/nonexistent/config.json')
        with self.assertRaises(RuntimeError):bridge.snapshot()
        bridge.frame=b'jpeg';bridge.updated=time.monotonic()
        self.assertEqual(bridge.snapshot(),b'jpeg')
        bridge.updated-=20
        with self.assertRaises(RuntimeError):bridge.snapshot()
    def test_status_does_not_expose_credentials(self):
        self.assertEqual(set(LSCBridge('/nonexistent').status()),{'configured','ready','frame_age_seconds','error','reconnects'})

"""Optional LSC1/H.264 to fresh JPEG bridge. Secrets stay in data/lsc-camera.json."""
import base64
import json
import logging
import os
from pathlib import Path
import shutil
import struct
import subprocess
import threading
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

MAX_RECORD = 2 * 1024 * 1024
MAX_JPEG = 4 * 1024 * 1024


def read_exact(stream, size):
    parts = bytearray()
    while len(parts) < size:
        chunk = stream.read(size - len(parts))
        if not chunk:
            if not parts:
                return None
            raise ValueError('Record LSC1 incompleto')
        parts.extend(chunk)
    return bytes(parts)


def records(stream):
    while True:
        header = read_exact(stream, 16)
        if header is None:
            return
        magic, timestamp, size = struct.unpack('>4sQI', header)
        if magic != b'LSC1' or not 0 < size <= MAX_RECORD:
            raise ValueError('Header LSC1 non valido')
        payload = read_exact(stream, size)
        if payload is None:
            raise ValueError('Payload LSC1 mancante')
        yield timestamp, payload


class LSCBridge:
    def __init__(self, config_path):
        self.path = Path(config_path)
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.thread = None
        self.process = None
        self.frame = None
        self.updated = 0
        self.error = 'Telecamera LSC non configurata'
        self.last_timestamp = None
        self.last_source_update = 0
        self.reconnects = 0

    def start(self):
        if self.path.exists():
            self.thread = threading.Thread(target=self.run, daemon=True, name='lsc-capture')
            self.thread.start()

    def snapshot(self, max_age=8):
        with self.lock:
            if not self.frame or time.monotonic() - self.updated > max_age:
                raise RuntimeError(self.error or 'Immagine LSC scaduta: riconnessione in corso')
            return self.frame

    def status(self):
        with self.lock:
            age = time.monotonic() - self.updated if self.updated else None
            return {'configured': self.path.exists(), 'ready': bool(self.frame and age < 8),
                    'frame_age_seconds': round(age, 2) if age is not None else None,
                    'error': self.error, 'reconnects': self.reconnects}

    def publish_jpegs(self, output):
        buffer = bytearray()
        while not self.stop.is_set():
            chunk = os.read(output.fileno(), 65536)
            if not chunk:
                return
            buffer.extend(chunk)
            while True:
                start = buffer.find(b'\xff\xd8')
                if start < 0:
                    if len(buffer) > MAX_JPEG:
                        raise ValueError('JPEG non valido')
                    break
                end = buffer.find(b'\xff\xd9', start + 2)
                if end < 0:
                    if len(buffer) > MAX_JPEG:
                        raise ValueError('JPEG troppo grande')
                    break
                frame = bytes(buffer[start:end + 2])
                del buffer[:end + 2]
                # Buffered/repeated camera records never refresh this timestamp.
                with self.lock:
                    self.frame = frame
                    self.updated = self.last_source_update
                    self.error = None

    def capture(self, config):
        url = config['url']
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('URL LSC non valido; credenziali in campi separati')
        binary = config.get('ffmpeg') or shutil.which('ffmpeg')
        if not binary:
            raise RuntimeError('FFmpeg non disponibile')
        auth = base64.b64encode((config['username'] + ':' + config['password']).encode()).decode()
        request = Request(url, headers={'Authorization': 'Basic ' + auth, 'Cache-Control': 'no-cache'})
        # A new decoder for each bounded camera request prevents broken GOPs across sessions.
        command = [binary, '-nostdin', '-hide_banner', '-loglevel', 'error',
                   '-probesize', '32768', '-analyzeduration', '0', '-flags', 'low_delay',
                   '-f', 'h264', '-i', 'pipe:0', '-an', '-vf', 'fps=3',
                   '-f', 'image2pipe', '-vcodec', 'mjpeg', '-q:v', '4', 'pipe:1']
        with urlopen(request, timeout=8) as response:
            with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, bufsize=0) as process:
                self.process = process
                reader = threading.Thread(target=self.publish_jpegs, args=(process.stdout,), daemon=True)
                reader.start()
                first = True
                try:
                    for timestamp, payload in records(response):
                        if self.stop.is_set():
                            break
                        # Camera reboot/time reset: discard the previous clock epoch.
                        if first and self.last_timestamp is not None and timestamp < self.last_timestamp - 60000:
                            self.last_timestamp = None
                        first = False
                        if self.last_timestamp is not None and timestamp <= self.last_timestamp:
                            continue
                        self.last_timestamp = timestamp
                        with self.lock:
                            self.last_source_update = time.monotonic()
                        view = memoryview(payload)
                        while view:
                            written = process.stdin.write(view)
                            if not written:
                                raise BrokenPipeError('Decoder interrotto')
                            view = view[written:]
                finally:
                    process.stdin.close()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    reader.join(timeout=3)
                    self.process = None
                if process.returncode:
                    raise RuntimeError('Decodifica video LSC non riuscita')

    def run(self):
        while not self.stop.is_set():
            try:
                config = json.loads(self.path.read_text())
                self.capture(config)
            except Exception as error:
                # Do not return remote URLs, credentials or request objects in the API/log.
                with self.lock:
                    self.error = 'Acquisizione LSC interrotta (' + type(error).__name__ + '); nuovo tentativo'
            self.reconnects += 1
            self.stop.wait(1)

    def close(self):
        self.stop.set()
        if self.process is not None:
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass
        if self.thread:
            self.thread.join(timeout=10)

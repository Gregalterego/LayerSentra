"""Opt-in PTZ bridge. URLs are administrator-defined locally, never supplied by clients."""
import json
import threading
from urllib.parse import urlsplit
import requests
from .config import ROOT

DIRECTIONS = ('left', 'right', 'up', 'down', 'stop')

class PTZ:
    def __init__(self, path=None):
        self.path = path or ROOT/'data/ptz.json'
        self.lock = threading.Lock()
    def settings(self):
        if not self.path.exists(): return None
        config = json.loads(self.path.read_text())
        if not isinstance(config,dict): raise ValueError('Configurazione PTZ non valida')
        if config.get('enabled') is not True: return None
        if config.get('bridge_auto_stop') is not True:
            raise ValueError('Il bridge PTZ deve garantire arresto autonomo entro un secondo.')
        if config.get('camera_id') not in ('primary','secondary'):
            raise ValueError('camera_id PTZ non valido')
        if not isinstance(config.get('commands'),dict) or set(config['commands']) != set(DIRECTIONS):
            raise ValueError('Configurare tutti i comandi PTZ, incluso stop')
        for url in config['commands'].values():
            if not isinstance(url,str): raise ValueError('URL bridge PTZ non valido')
            parsed=urlsplit(url)
            if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
                raise ValueError('URL bridge PTZ non valido')
        return config
    def availability(self):
        try:
            config = self.settings()
            return {'enabled': bool(config), 'camera_id':config['camera_id'] if config else None,
                    'reason':None if config else 'Movimento LSC non configurato: serve un bridge PTZ verificato.'}
        except (ValueError, OSError) as error:
            return {'enabled':False,'camera_id':None,'reason':str(error)}
    def move(self, direction):
        if direction not in DIRECTIONS: raise ValueError('Direzione PTZ non valida')
        config = self.settings()
        if not config: raise ValueError('Movimento telecamera non configurato')
        if not self.lock.acquire(blocking=False): raise ValueError('Movimento già in corso')
        try:
            # The bridge contract requires each directional POST to be a bounded pulse.
            # It MUST stop independently even when PrintWatch or the network disappears.
            response=requests.post(config['commands'][direction],json={'duration_ms':200},timeout=(2,2),allow_redirects=False)
            if response.status_code not in (200,204): raise ValueError('Il bridge PTZ non ha confermato il comando')
        finally:
            self.lock.release()

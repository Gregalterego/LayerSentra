import copy
import json
import math
import os
from pathlib import Path

CATEGORIES = ('spaghetti', 'blob', 'warping', 'crack')
ROOT = Path(__file__).resolve().parents[1]
DEFAULT = {
    'moonraker_url': 'http://127.0.0.1:7125', 'interval_seconds': 3,
    'monitoring': False, 'action': 'observe', 'warmup_seconds': 30,
    'cooldown_seconds': 120, 'max_frame_age_seconds': 10,
    'model_path': 'models/model.tflite', 'resize_mode': 'stretch',
    'nms_iou': 0.45, 'window_seconds': 20, 'minimum_hits': 3,
    'minimum_duration_seconds': 6,
    'cameras': [
        {'id': 'primary', 'name': 'Primary camera', 'enabled': True,
         'url': 'http://127.0.0.1/webcam/?action=snapshot', 'roi': [0, 0, 1, 1], 'masks': []},
        {'id': 'secondary', 'name': 'Secondary camera', 'enabled': False, 'url': '',
         'roi': [0, 0, 1, 1], 'masks': []}],
    'filament': {'diameter_mm':1.75,'density_g_cm3':1.27,'low_warning_g':100},
    'categories': {c: {'enabled': True, 'threshold': 0.7,
                       'minimum_area': 0.0002, 'maximum_area': 0.8,
                       'can_pause': c == 'spaghetti'} for c in CATEGORIES}
}

def number(value, lo, hi, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lo <= value <= hi:
        raise ValueError(f'{name}: valore richiesto tra {lo} e {hi}')

def rectangle(r):
    if not isinstance(r, list) or len(r) != 4:
        raise ValueError('Rettangolo richiesto: [x, y, larghezza, altezza]')
    for v in r: number(v, 0, 1, 'coordinate')
    if r[2] <= 0 or r[3] <= 0 or r[0]+r[2] > 1.000001 or r[1]+r[3] > 1.000001:
        raise ValueError('Rettangolo fuori immagine o vuoto')

def validate(c):
    if set(c) != set(DEFAULT): raise ValueError('Campi configurazione mancanti o sconosciuti')
    if c['action'] not in ('observe', 'pause'): raise ValueError('Azione non valida')
    if type(c['monitoring']) is not bool: raise ValueError('monitoring deve essere booleano')
    if c['resize_mode'] not in ('stretch', 'letterbox'): raise ValueError('Resize non valido')
    for k, lo, hi in [('interval_seconds',1,60), ('warmup_seconds',0,600),
                     ('cooldown_seconds',10,3600), ('max_frame_age_seconds',1,60),
                     ('nms_iou',0.05,0.95), ('window_seconds',2,300),
                     ('minimum_hits',2,100), ('minimum_duration_seconds',1,120)]:
        number(c[k],lo,hi,k)
    if int(c['minimum_hits']) != c['minimum_hits']: raise ValueError('minimum_hits deve essere intero')
    if c['minimum_duration_seconds'] > c['window_seconds']: raise ValueError('Durata superiore alla finestra')
    if not isinstance(c['model_path'],str) or not c['model_path']: raise ValueError('Percorso modello non valido')
    from urllib.parse import urlsplit
    def url(u, schemes):
        p=urlsplit(u)
        if p.scheme not in schemes or not p.hostname or p.username or p.password:
            raise ValueError('URL non valido; non inserire credenziali nell’URL')
    url(c['moonraker_url'], ('http','https'))
    if not isinstance(c['cameras'],list) or not 1 <= len(c['cameras']) <= 4: raise ValueError('Da 1 a 4 telecamere')
    ids=set()
    for cam in c['cameras']:
        if set(cam) != {'id','name','enabled','url','roi','masks'}: raise ValueError('Campi telecamera non validi')
        if not isinstance(cam['id'],str) or not cam['id'].isalnum() or cam['id'] in ids: raise ValueError('ID telecamera non valido')
        ids.add(cam['id'])
        if not isinstance(cam['name'],str) or type(cam['enabled']) is not bool: raise ValueError('Nome/stato telecamera non valido')
        if cam['enabled']: url(cam['url'], ('http','https','rtsp'))
        rectangle(cam['roi'])
        if not isinstance(cam['masks'],list) or len(cam['masks']) > 20: raise ValueError('Massimo 20 maschere')
        for r in cam['masks']: rectangle(r)
    if set(c['filament']) != {'diameter_mm','density_g_cm3','low_warning_g'}: raise ValueError('Campi filamento non validi')
    for k,lo,hi in [('diameter_mm',1,4),('density_g_cm3',0.5,3),('low_warning_g',0,5000)]:
        number(c['filament'][k],lo,hi,k)
    if set(c['categories']) != set(CATEGORIES): raise ValueError('Categorie non valide')
    for name, rule in c['categories'].items():
        if set(rule) != {'enabled','threshold','minimum_area','maximum_area','can_pause'}: raise ValueError('Regola non valida')
        if type(rule['enabled']) is not bool or type(rule['can_pause']) is not bool: raise ValueError('Regola booleana non valida')
        for k in ('threshold','minimum_area','maximum_area'): number(rule[k],0,1,name+'.'+k)
        if rule['minimum_area'] >= rule['maximum_area']: raise ValueError('Area minima >= massima')
    return c

def load(path):
    if not path.exists(): return copy.deepcopy(DEFAULT)
    c=json.loads(path.read_text())
    c.setdefault('filament',copy.deepcopy(DEFAULT['filament']))
    return validate(c)

def save(path, c):
    validate(c)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(c, indent=2)+'\n')
    os.chmod(temp, 0o600)
    os.replace(temp,path)

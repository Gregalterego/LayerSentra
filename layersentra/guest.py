"""Separate, opt-in guest service. Never proxy arbitrary printer paths."""
import argparse
import hashlib
import io
import json
import math
import os
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests
from flask import Flask, jsonify, request, send_file, session
from .config import ROOT, load
from .io import Moonraker

SETTINGS = ROOT / 'data/guest-access.json'
BACKEND = 'http://127.0.0.1:7127'


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def read_settings(path):
    cfg = json.loads(path.read_text())
    parsed = urlsplit(cfg['origin'])
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment):
        raise ValueError('Serve una origine HTTPS senza percorso')
    if len(cfg['token_hash']) != 64 or len(cfg['session_key']) < 43:
        raise ValueError('Chiavi ospite non valide')
    if cfg['camera_id'] not in ('primary', 'secondary'):
        raise ValueError('Camera non valida')
    ids = cfg.get('camera_ids', [cfg['camera_id']])
    if not isinstance(ids, list) or not ids or len(ids) > 2 or any(cid not in ('primary', 'secondary') for cid in ids) or len(set(ids)) != len(ids):
        raise ValueError('Camere ospite non valide')
    cfg['camera_ids'] = ids
    expiry = cfg.get('expires_at', 'missing')
    if expiry is not None and (isinstance(expiry, bool) or not isinstance(expiry, (int, float))
                               or not math.isfinite(expiry)):
        raise ValueError('Scadenza ospite non valida')
    return cfg


def create_app(settings_path=SETTINGS):
    settings_path = Path(settings_path)
    initial = read_settings(settings_path)
    app = Flask(__name__, static_folder=None)
    app.secret_key = initial['session_key']
    app.config.update(MAX_CONTENT_LENGTH=1024, SESSION_COOKIE_NAME='__Host-layersentra_guest',
                      SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Strict')
    action_lock = threading.Lock()
    rate_lock = threading.Lock()
    last = {}
    holds = {}
    hold_lock = threading.Lock()

    def allowed_rate(key, seconds):
        with rate_lock:
            now = time.monotonic()
            if now - last.get(key, -float('inf')) < seconds:
                return False
            last[key] = now
            return True

    def cfg_now():
        cfg = read_settings(settings_path)
        if cfg.get('enabled') is not True or (cfg['expires_at'] is not None and cfg['expires_at'] <= time.time()):
            raise ValueError('Invito scaduto o revocato')
        return cfg

    @app.before_request
    def guard():
        try:
            cfg = cfg_now()
        except (OSError, ValueError, KeyError, TypeError):
            return jsonify(error='Accesso ospite non disponibile'), 403
        if request.host != urlsplit(cfg['origin']).netloc:
            return jsonify(error='Host non consentito'), 403
        if request.method not in ('GET', 'POST'):
            return jsonify(error='Metodo non consentito'), 405
        if request.method == 'POST' and (request.headers.get('Origin') != cfg['origin'] or not request.is_json):
            return jsonify(error='Origine o formato non consentiti'), 403
        # Explicit allowlist is enforced before routing, including all unknown paths.
        if request.path not in ('/', '/guest.js', '/guest.css', '/session', '/api/status',
                                '/api/frame', '/api/frame/primary', '/api/frame/secondary',
                                '/api/hold', '/api/hold/cancel', '/api/pause', '/api/resume'):
            return jsonify(error='Operazione non consentita'), 403
        if request.path.startswith('/api/frame/') and request.path.rsplit('/',1)[1] not in cfg['camera_ids']:
            return jsonify(error='Camera non consentita'), 403
        if request.path in ('/', '/guest.js', '/guest.css', '/session'):
            return
        if (session.get('grant') != cfg['token_hash'] or session.get('until', 0) <= time.time()):
            return jsonify(error='Accesso scaduto: riaprire il link di invito'), 401
        if request.method == 'POST' and not secrets.compare_digest(
                request.headers.get('X-Guest-CSRF', ''), session.get('csrf', 'missing')):
            return jsonify(error='Richiesta non autorizzata'), 403

    @app.after_request
    def headers(response):
        response.headers.update({'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer',
            'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY',
            'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"})
        return response

    @app.get('/')
    def index():
        return send_file(ROOT / 'guest/index.html')

    @app.get('/guest.js')
    def script():
        return send_file(ROOT / 'guest/guest.js')

    @app.get('/guest.css')
    def style():
        return send_file(ROOT / 'guest/guest.css')

    @app.post('/session')
    def login():
        # Global bound, independent of attacker-controlled forwarded headers/cookies.
        if not allowed_rate('login', 1):
            return jsonify(error='Attendere un secondo'), 429
        body = request.get_json(silent=True)
        cfg = cfg_now()
        if (not isinstance(body, dict) or set(body) != {'token'} or not isinstance(body['token'], str)
                or not secrets.compare_digest(digest(body['token']), cfg['token_hash'])):
            return jsonify(error='Invito non valido'), 403
        session.clear()
        until = time.time() + 8 * 3600
        if cfg['expires_at'] is not None:
            until = min(until, cfg['expires_at'])
        session.update(grant=cfg['token_hash'], until=until,
                       csrf=secrets.token_urlsafe(32))
        return jsonify(ok=True)

    def backend_json(path):
        response = requests.get(BACKEND + path, timeout=(2, 5), allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError('Backend non disponibile')
        return response.json()

    @app.get('/api/status')
    def status():
        try:
            data = backend_json('/api/status')
            cfg = cfg_now()
            cameras = []
            for cid in cfg['camera_ids']:
                camera = data.get('cameras', {}).get(cid, {})
                age = time.time() - (camera.get('captured_at') or 0)
                cameras.append(dict(id=cid, name='Telecamera stampante' if cid == 'primary' else 'Telecamera LSC',
                                    ready=camera.get('state') == 'ok' and 0 <= age <= 10))
            return jsonify(state=data.get('printer', {}).get('state', 'unknown'),
                           printer_ready=data.get('printer', {}).get('fresh') is True,
                           camera_ready=any(c['ready'] for c in cameras), cameras=cameras,
                           can_resume=cfg.get('can_resume') is True, hold_seconds=5, csrf=session['csrf'])
        except Exception:
            return jsonify(error='Server o telecamera non disponibili'), 503

    @app.get('/api/frame', defaults={'camera_id': None})
    @app.get('/api/frame/<camera_id>')
    def frame(camera_id):
        try:
            cfg = cfg_now()
            cid = camera_id or cfg['camera_id']
            if cid not in cfg['camera_ids']:
                return jsonify(error='Camera non consentita'), 403
            data = backend_json('/api/status').get('cameras', {}).get(cid, {})
            age = time.time() - (data.get('captured_at') or 0)
            if data.get('state') != 'ok' or not 0 <= age <= 10:
                raise RuntimeError('Frame non aggiornato')
            response = requests.get(BACKEND + '/api/frame/' + cid, timeout=(2, 5),
                                    allow_redirects=False, stream=True)
            with response:
                if response.status_code != 200 or not response.headers.get('Content-Type', '').startswith('image/jpeg'):
                    raise RuntimeError('Frame non disponibile')
                parts, size = [], 0
                for chunk in response.iter_content(65536):
                    size += len(chunk)
                    if size > 12 * 1024 * 1024:
                        raise RuntimeError('Frame troppo grande')
                    parts.append(chunk)
            return send_file(io.BytesIO(b''.join(parts)), mimetype='image/jpeg')
        except Exception:
            return jsonify(error='Immagine non aggiornata o non disponibile'), 503

    @app.post('/api/hold')
    def begin_hold():
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {'action'} or body['action'] not in ('pause', 'resume'):
            return jsonify(error='Azione non valida'), 400
        if body['action'] == 'resume' and cfg_now().get('can_resume') is not True:
            return jsonify(error='Ripresa ospite non abilitata'), 403
        now = time.monotonic()
        with hold_lock:
            for token, hold in list(holds.items()):
                if now - hold['started'] > 20 or hold['session'] == session['csrf']:
                    holds.pop(token)
            if len(holds) >= 256:
                return jsonify(error='Troppe richieste: riprovare'), 429
            token = secrets.token_urlsafe(32)
            holds[token] = dict(started=now, session=session['csrf'], action=body['action'])
        return jsonify(hold_token=token, seconds=5)

    @app.post('/api/hold/cancel')
    def cancel_hold():
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {'hold_token'} or not isinstance(body['hold_token'], str):
            return jsonify(error='Richiesta non valida'), 400
        with hold_lock:
            hold = holds.get(body['hold_token'])
            if hold and hold['session'] == session['csrf']:
                holds.pop(body['hold_token'])
        return jsonify(ok=True)

    def execute_action(action):
        if action == 'resume' and cfg_now().get('can_resume') is not True:
            return jsonify(error='Ripresa ospite non abilitata'), 403
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {'hold_token'} or not isinstance(body['hold_token'], str):
            return jsonify(error='Tenere premuto il pulsante per cinque secondi'), 400
        with hold_lock:
            hold = holds.get(body['hold_token'])
            if not hold or hold['session'] != session['csrf']:
                return jsonify(error='Pressione non valida o gia utilizzata'), 409
            holds.pop(body['hold_token'])
        elapsed = time.monotonic() - hold['started']
        if hold['action'] != action or not 5 <= elapsed <= 20:
            return jsonify(error='Pressione troppo breve, scaduta o azione diversa'), 409
        if not allowed_rate('printer-action', 5):
            return jsonify(error='Comando gia richiesto: verificare lo stato'), 429
        if not action_lock.acquire(blocking=False):
            return jsonify(error='Richiesta in corso'), 409
        try:
            moonraker = Moonraker(load(ROOT / 'data/config.json')['moonraker_url'])
            state = moonraker.status()
            required = 'printing' if action == 'pause' else 'paused'
            if state.get('fresh') is False or state.get('state') != required:
                return jsonify(error='Stato stampante cambiato: verificare prima di riprovare'), 409
            if action == 'pause':
                moonraker.pause()
            else:
                moonraker.resume()
            return jsonify(ok=True, state='paused' if action == 'pause' else 'printing')
        except Exception:
            return jsonify(error='Comando non confermato: controllare la stampante'), 502
        finally:
            action_lock.release()

    @app.post('/api/pause')
    def pause():
        return execute_action('pause')

    @app.post('/api/resume')
    def resume():
        return execute_action('resume')

    return app


def main():
    parser = argparse.ArgumentParser(description='Crea un invito ospite privato, senza attivare rete o servizi')
    parser.add_argument('--origin', required=True, help='Origine HTTPS dedicata agli ospiti')
    parser.add_argument('--camera', choices=['primary', 'secondary'], default='secondary')
    parser.add_argument('--hours', type=int, default=24)
    parser.add_argument('--permanent', action='store_true', help='Invito senza scadenza automatica, sempre revocabile')
    args = parser.parse_args()
    if not 1 <= args.hours <= 168:
        parser.error('Durata tra 1 e 168 ore')
    token = secrets.token_urlsafe(32)
    cfg = dict(origin=args.origin, camera_id=args.camera, enabled=True,
               expires_at=None if args.permanent else time.time() + args.hours * 3600, token_hash=digest(token),
               session_key=secrets.token_urlsafe(48))
    SETTINGS.parent.mkdir(exist_ok=True)
    # Refuse replacement: revocation/rotation must be deliberate on the host.
    fd = os.open(SETTINGS, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w') as file:
            json.dump(cfg, file)
        read_settings(SETTINGS)
    except Exception:
        SETTINGS.unlink(missing_ok=True)
        raise
    print('Invito riservato (chi possiede il link può usare video e pausa):')
    print(args.origin + '/#invite=' + token)
    print('Non ancora pubblicato: configurare e collaudare il servizio HTTPS separato.')


if __name__ == '__main__':
    main()

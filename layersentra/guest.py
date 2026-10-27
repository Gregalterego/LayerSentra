"""Separate, opt-in guest service. Never proxy arbitrary printer paths."""
import argparse
import hashlib
import io
import json
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

    def allowed_rate(key, seconds):
        with rate_lock:
            now = time.monotonic()
            if now - last.get(key, -float('inf')) < seconds:
                return False
            last[key] = now
            return True

    def cfg_now():
        cfg = read_settings(settings_path)
        if cfg.get('enabled') is not True or cfg['expires_at'] <= time.time():
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
                                '/api/frame', '/api/ptz', '/api/pause'):
            return jsonify(error='Operazione non consentita'), 403
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
        session.update(grant=cfg['token_hash'], until=min(time.time() + 8 * 3600, cfg['expires_at']),
                       csrf=secrets.token_urlsafe(32))
        return jsonify(ok=True)

    def backend_json(path):
        response = requests.get(BACKEND + path, timeout=(2, 5), allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError('Backend non disponibile')
        return response.json()

    def ptz_info():
        config = backend_json('/api/config')
        ptz = config.get('capabilities', {}).get('ptz', {})
        return config, bool(ptz.get('enabled') is True
                            and ptz.get('camera_id') == cfg_now()['camera_id']
                            and config.get('ptz_token'))

    @app.get('/api/status')
    def status():
        try:
            data = backend_json('/api/status')
            _, enabled = ptz_info()
            cid = cfg_now()['camera_id']
            camera = data.get('cameras', {}).get(cid, {})
            age = time.time() - (camera.get('captured_at') or 0)
            fresh = camera.get('state') == 'ok' and 0 <= age <= 10
            return jsonify(state=data.get('printer', {}).get('state', 'unknown'),
                           camera_ready=fresh, ptz=enabled, csrf=session['csrf'])
        except Exception:
            return jsonify(error='Server o telecamera non disponibili'), 503

    @app.get('/api/frame')
    def frame():
        try:
            cid = cfg_now()['camera_id']
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

    @app.post('/api/ptz')
    def ptz():
        body = request.get_json(silent=True)
        if (not isinstance(body, dict) or set(body) != {'direction'}
                or body['direction'] not in ('left', 'right', 'up', 'down', 'stop')):
            return jsonify(error='Direzione non valida'), 400
        if body['direction'] != 'stop' and not allowed_rate('ptz', 1):
            return jsonify(error='Attendere un secondo'), 429
        try:
            config, enabled = ptz_info()
            if not enabled:
                return jsonify(error='PTZ non collaudato o non configurato'), 409
            response = requests.post(BACKEND + '/api/ptz', json=body,
                headers={'X-LayerSentra-Token': config['ptz_token']},
                timeout=(2, 6), allow_redirects=False)
            if response.status_code != 200:
                raise RuntimeError('PTZ non confermato')
            return jsonify(ok=True)
        except Exception:
            return jsonify(error='Comando telecamera non confermato'), 502

    @app.post('/api/pause')
    def pause():
        # Fixed action only. No G-code, URL, resume, cancel or configuration payloads.
        if request.get_json(silent=True) != {}:
            return jsonify(error='La pausa non accetta parametri'), 400
        if not allowed_rate('pause', 5):
            return jsonify(error='Pausa già richiesta: verificare lo stato'), 429
        if not action_lock.acquire(blocking=False):
            return jsonify(error='Richiesta in corso'), 409
        try:
            moonraker = Moonraker(load(ROOT / 'data/config.json')['moonraker_url'])
            if moonraker.status().get('state') == 'paused':
                return jsonify(ok=True, state='paused')
            moonraker.pause()  # Rechecks live state and confirms paused, never resumes.
            return jsonify(ok=True, state='paused')
        except Exception:
            return jsonify(error='Pausa non confermata: controllare la stampante'), 502
        finally:
            action_lock.release()

    return app


def main():
    parser = argparse.ArgumentParser(description='Crea un invito ospite privato, senza attivare rete o servizi')
    parser.add_argument('--origin', required=True, help='Origine HTTPS dedicata agli ospiti')
    parser.add_argument('--camera', choices=['primary', 'secondary'], default='secondary')
    parser.add_argument('--hours', type=int, default=24)
    args = parser.parse_args()
    if not 1 <= args.hours <= 168:
        parser.error('Durata tra 1 e 168 ore')
    token = secrets.token_urlsafe(32)
    cfg = dict(origin=args.origin, camera_id=args.camera, enabled=True,
               expires_at=time.time() + args.hours * 3600, token_hash=digest(token),
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
    print('Invito riservato (chi possiede il link può usare video, PTZ e pausa):')
    print(args.origin + '/#invite=' + token)
    print('Non ancora pubblicato: configurare e collaudare il servizio HTTPS separato.')


if __name__ == '__main__':
    main()

import copy
import io
import json
import logging
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
from flask import Flask, jsonify, request, send_file, g
from .config import ROOT, load, save, validate
from .decision import DecisionEngine, pause_allowed
from .io import Moonraker, snapshot
from .filament import Spool
from .lsc import LSCBridge
from .access import proxy_identity
from .ptz import PTZ

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
CONFIG_PATH=ROOT/'data/config.json'
DB_PATH=ROOT/'data/events.sqlite3'
DB_PATH.parent.mkdir(exist_ok=True)
TOKEN=secrets.token_urlsafe(32)
OBSERVATION_TOKEN=secrets.token_urlsafe(32)
PTZ_TOKEN=secrets.token_urlsafe(32)
ptz=PTZ()
MOBILE_PATH=ROOT/'data/mobile-access.json'
MOBILE=json.loads(MOBILE_PATH.read_text()) if MOBILE_PATH.exists() else {}
app=Flask(__name__,static_folder=str(ROOT/'static'),static_url_path='/static')
app.config['MAX_CONTENT_LENGTH']=65536

class Monitor:
    def __init__(self):
        self.lock=threading.RLock(); self.config=load(CONFIG_PATH)
        # Pause is never armed just because the program restarted.
        self.config['action']='observe'; self.config['monitoring']=False
        self.spool=Spool(ROOT/'data/spool.json')
        self.generation=0; self.engine=DecisionEngine(); self.detector=None
        self.status={'model':'loading','model_error':None,'printer':{'state':'unknown','fresh':False},'cameras':{},'last_action':None}
        self.frames={}; self.stop=threading.Event(); self.armed_at=time.monotonic()
        self.cooldown_at=-float('inf'); self.event_at={}; self.fingerprints={}; self.print_id=None; self.last_print_state=None
        self.action_attempted=False; self.last_tick=None
        with sqlite3.connect(DB_PATH) as db:
            db.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, time TEXT, camera TEXT, category TEXT, score REAL, mode TEXT, detail TEXT)')

    def event(self,camera,category,score,mode,detail):
        with sqlite3.connect(DB_PATH) as db:
            db.execute('INSERT INTO events(time,camera,category,score,mode,detail) VALUES(?,?,?,?,?,?)',
                       (datetime.now(timezone.utc).isoformat(),camera,category,score,mode,detail))
            db.execute('DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 2000)')

    def configure(self,c):
        validate(c)
        with self.lock:
            if c['model_path'] != self.config['model_path']: raise ValueError('Cambiare modello richiede arresto e riavvio del programma')
            save(CONFIG_PATH,c); self.config=copy.deepcopy(c); self.generation+=1
            self.engine.reset(); self.armed_at=time.monotonic(); self.fingerprints.clear()
            self.action_attempted=False; self.event_at.clear()

    def run(self):
        try:
            from .detector import Detector
            self.detector=Detector(ROOT/self.config['model_path'])
            self.status['model']='ready'
        except Exception as error:
            logging.exception('Modello non disponibile')
            self.status['model']='unavailable'; self.status['model_error']=str(error)
        while not self.stop.is_set():
            start=time.monotonic()
            try: self.tick()
            except Exception:
                logging.exception('Errore ciclo monitoraggio')
                with self.lock: self.engine.reset()
            with self.lock: interval=self.config['interval_seconds']; self.last_tick=time.time()
            self.stop.wait(max(0.1,interval-(time.monotonic()-start)))

    def tick(self):
        with self.lock: cfg=copy.deepcopy(self.config); generation=self.generation
        try: printer=Moonraker(cfg['moonraker_url']).status()
        except Exception as error: printer={'state':'unknown','fresh':False,'error':str(error)}
        with self.lock:
            self.status['printer']=printer
            self.status['filament']=self.spool.update(printer,cfg['filament'])
            current_id=printer.get('filename')
            if current_id != self.print_id or (printer['state']=='printing' and self.last_print_state != 'printing'):
                self.engine.reset(); self.armed_at=time.monotonic()
                if current_id != self.print_id: self.action_attempted=False
            self.print_id=current_id; self.last_print_state=printer['state']
        for camera in cfg['cameras']:
            cid=camera['id']
            if not camera['enabled']:
                with self.lock:
                    self.status['cameras'][cid]={'state':'disabled'}; self.frames.pop(cid,None); self.engine.reset(cid)
                continue
            captured=time.monotonic()
            try:
                image,digest=snapshot(camera['url'])
                now=time.monotonic()
                previous=self.fingerprints.get(cid)
                unchanged=previous and previous[0]==digest
                changed_at=previous[1] if unchanged else now
                self.fingerprints[cid]=(digest,changed_at)
                stale=now-changed_at>cfg['max_frame_age_seconds']
                detections=[]; latency=None
                analyse=cfg['monitoring'] and self.detector is not None and printer['fresh'] and printer['state']=='printing' and not stale
                if analyse: detections,latency=self.detector.infer(image,camera,cfg)
                from PIL import ImageDraw
                draw=ImageDraw.Draw(image)
                for d in detections:
                    x,y,w,h=d['box']; iw,ih=image.size
                    draw.rectangle((x*iw,y*ih,(x+w)*iw,(y+h)*ih),outline='#fbbf24',width=max(2,iw//400))
                    draw.text((x*iw,max(0,y*ih-14)),f"{d['category']} {d['score']:.0%}",fill='#fbbf24')
                buffer=io.BytesIO(); image.save(buffer,'JPEG',quality=85)
                with self.lock:
                    if generation != self.generation: continue
                    self.frames[cid]=buffer.getvalue()
                    confirmed,progress=self.engine.update(cid,detections,time.monotonic(),cfg) if analyse else ([],{})
                    if not analyse: self.engine.reset(cid)
                    self.status['cameras'][cid]={'state':'stale' if stale else 'ok','captured_at':time.time(),
                        'detections':detections,'confirmation':progress,'inference_ms':latency,'analysing':analyse}
                    for d in confirmed:
                        key=(cid,d['category']); moment=time.monotonic()
                        if moment-self.event_at.get(key,-float('inf'))<cfg['cooldown_seconds']: continue
                        self.event_at[key]=moment
                        self.event(cid,d['category'],d['score'],'confirmed','Conferma temporale; punteggio modello non calibrato')
                        permitted=(cfg['categories'][d['category']]['can_pause'] and not self.action_attempted
                            and pause_allowed(cfg,printer,moment-self.armed_at,moment-captured,True,moment-self.cooldown_at))
                        if permitted:
                            # Serialize config changes and action; only one automatic attempt per arming.
                            self.action_attempted=True; self.cooldown_at=moment
                            try:
                                Moonraker(cfg['moonraker_url']).pause()
                                detail='Pausa confermata da Moonraker'
                                self.event(cid,d['category'],d['score'],'paused',detail)
                            except Exception as error:
                                detail='Pausa non confermata: '+str(error)
                                self.event(cid,d['category'],d['score'],'action_error',detail)
                            self.status['last_action']=detail
            except Exception as error:
                with self.lock:
                    self.engine.reset(cid); self.frames.pop(cid,None)
                    self.status['cameras'][cid]={'state':'error','error':str(error),'captured_at':None}

monitor=Monitor()
lsc_bridge=LSCBridge(ROOT/"data/lsc-camera.json")

@app.before_request
def local_access():
    g.mobile=False
    local_hosts=('127.0.0.1:7127','localhost:7127')
    if request.host not in local_hosts:
        allowed_host=MOBILE.get('hostname')
        host=request.host.removesuffix(':443')
        if not proxy_identity(request.host, request.remote_addr, request.headers, MOBILE) and (not allowed_host or host != allowed_host
            or request.remote_addr not in ('127.0.0.1','::1')
            or not MOBILE.get('login')
            or request.headers.get('Tailscale-User-Login') != MOBILE['login']):
            return jsonify(error='Accesso remoto autenticato richiesto'),403
        g.mobile=True
        if request.method not in ('GET','HEAD') and request.path not in ('/api/observation','/api/ptz'):
            return jsonify(error='La vista telefono è di sola lettura'),403
    origin=request.headers.get('Origin')
    expected=('https://'+MOBILE['hostname']) if g.mobile else request.host_url.rstrip('/')
    if origin and origin != expected:
        return jsonify(error='Origine non consentita'),403
    if request.method=='POST':
        expected_token=OBSERVATION_TOKEN if request.path == '/api/observation' else PTZ_TOKEN if request.path == '/api/ptz' else TOKEN
        if not request.is_json or not secrets.compare_digest((request.headers.get('X-LayerSentra-Token') or request.headers.get('X-PrintWatch-Token','')),expected_token):
            return jsonify(error='Richiesta non autorizzata: ricaricare il pannello'),403

@app.get('/')
def index(): return app.send_static_file('index.html')

@app.get('/api/status')
def status():
    with monitor.lock:
        result=copy.deepcopy(monitor.status)
        result.update(monitoring=monitor.config['monitoring'],action=monitor.config['action'],last_tick=monitor.last_tick)
    return jsonify(result)

@app.get('/api/config')
def config_get():
    with monitor.lock:
        cfg=copy.deepcopy(monitor.config)
        if g.mobile:
            cfg['moonraker_url']=''
            for camera in cfg['cameras']: camera['url']=''
        ptz_status=ptz.availability()
        return jsonify(config=cfg,token=None if g.mobile else TOKEN,read_only=g.mobile,observation_token=OBSERVATION_TOKEN,ptz_token=PTZ_TOKEN if ptz_status['enabled'] else None,capabilities={'observation_control':True,'ptz':ptz_status},server_version='0.6.0')

@app.post('/api/ptz')
def ptz_post():
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict) or set(payload) != {'direction'}:
        return jsonify(error='Richiesta una sola direzione'),400
    try:
        ptz.move(payload['direction'])
        with monitor.lock:
            monitor.generation+=1
            monitor.engine.reset()
            monitor.fingerprints.clear()
            monitor.frames.clear()
            monitor.armed_at=time.monotonic()
        return jsonify(ok=True)
    except (ValueError,TypeError) as error:
        return jsonify(error=str(error)),400
    except Exception:
        return jsonify(error='Bridge PTZ non raggiungibile; verificare la telecamera'),502

@app.post('/api/observation')
def observation_post():
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict) or set(payload) != {'enabled'} or type(payload['enabled']) is not bool:
        return jsonify(error='Richiesto soltanto enabled: true/false'),400
    with monitor.lock:
        cfg=copy.deepcopy(monitor.config)
        cfg['monitoring']=payload['enabled']
        cfg['action']='observe'
        monitor.configure(cfg)
    return jsonify(ok=True,monitoring=cfg['monitoring'],action='observe')

@app.post('/api/config')
def config_post():
    try: monitor.configure(request.get_json()); return jsonify(ok=True)
    except (ValueError,TypeError,KeyError,AttributeError) as error: return jsonify(error=str(error)),400

@app.get('/api/lsc/snapshot')
def lsc_snapshot():
    try: raw=lsc_bridge.snapshot()
    except RuntimeError as error: return jsonify(error=str(error)),503
    response=send_file(io.BytesIO(raw),mimetype='image/jpeg')
    response.headers['Cache-Control']='no-store'
    return response

@app.get('/api/lsc/status')
def lsc_status(): return jsonify(lsc_bridge.status())

@app.get('/api/frame/<cid>')
def frame(cid):
    with monitor.lock:
        raw=monitor.frames.get(cid)
        state=monitor.status['cameras'].get(cid,{})
        if not raw or time.time()-state.get('captured_at',0)>monitor.config['max_frame_age_seconds']:
            return jsonify(error='Fotogramma non disponibile o scaduto'),503
    response=send_file(io.BytesIO(raw),mimetype='image/jpeg'); response.headers['Cache-Control']='no-store'; return response

@app.post('/api/filament')
def set_filament():
    try:
        payload=request.get_json()
        with monitor.lock:
            cfg=copy.deepcopy(monitor.config)
            cfg['filament']={key:payload[key] for key in ('diameter_mm','density_g_cm3','low_warning_g')}
            validate(cfg)
            printer=Moonraker(cfg['moonraker_url']).status()
            monitor.spool.set_remaining(payload['remaining_g'],printer)
            monitor.configure(cfg)
            monitor.status['filament']=monitor.spool.update(printer,cfg['filament'])
        return jsonify(ok=True)
    except (ValueError,TypeError,KeyError) as error: return jsonify(error=str(error)),400
    except Exception as error: return jsonify(error='Impossibile leggere il consumo attuale: '+str(error)),503

@app.get('/api/events')
def events():
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory=sqlite3.Row
        rows=[dict(r) for r in db.execute('SELECT * FROM events ORDER BY id DESC LIMIT 100')]
    return jsonify(rows)

@app.get('/api/events/export')
def export():
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory=sqlite3.Row; rows=[dict(r) for r in db.execute('SELECT * FROM events ORDER BY id')]
    return send_file(io.BytesIO(json.dumps(rows,indent=2).encode()),mimetype='application/json',as_attachment=True,download_name='layersentra-events.json')

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--observe',action='store_true',help='Avvia analisi in sola osservazione')
    args=parser.parse_args()
    if args.observe:
        monitor.config['monitoring']=True
        monitor.config['action']='observe'
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    import subprocess,sys
    gateway=subprocess.Popen([sys.executable,'-m','layersentra.gateway'],cwd=ROOT)
    lsc_bridge.start()
    thread=threading.Thread(target=monitor.run,daemon=True); thread.start()
    try: app.run(host='127.0.0.1',port=7127,debug=False,use_reloader=False,threaded=True)
    finally:
        monitor.stop.set(); thread.join(timeout=12)
        lsc_bridge.close()
        gateway.terminate()
        try: gateway.wait(timeout=5)
        except subprocess.TimeoutExpired: gateway.kill(); gateway.wait()

if __name__=='__main__': main()

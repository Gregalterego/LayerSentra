import hashlib
import io
import shutil
import subprocess
import time
from urllib.parse import urlsplit
import requests
from PIL import Image

MAX_IMAGE=12*1024*1024

def snapshot(url):
    if urlsplit(url).scheme == 'rtsp':
        binary=shutil.which('ffmpeg')
        if not binary: raise RuntimeError('RTSP richiede FFmpeg; usare intanto una sorgente HTTP snapshot')
        result=subprocess.run([binary,'-nostdin','-loglevel','error','-rtsp_transport','tcp',
            '-i',url,'-frames:v','1','-vf','scale=1920:1920:force_original_aspect_ratio=decrease',
            '-f','image2pipe','-vcodec','mjpeg','pipe:1'],capture_output=True,timeout=8,check=True)
        raw=result.stdout
        if len(raw)>MAX_IMAGE: raise ValueError('Fotogramma troppo grande')
    else:
        start=time.monotonic(); parts=[]; size=0
        with requests.get(url,timeout=(3,4),stream=True,headers={'Cache-Control':'no-cache'}) as response:
            response.raise_for_status()
            if not response.headers.get('Content-Type','').lower().startswith('image/'):
                raise ValueError('La sorgente deve restituire una singola immagine, non una pagina o uno stream MJPEG')
            for chunk in response.iter_content(65536):
                size+=len(chunk)
                if size>MAX_IMAGE or time.monotonic()-start>6: raise ValueError('Fotogramma troppo grande o risposta lenta')
                parts.append(chunk)
        raw=b''.join(parts)
    with Image.open(io.BytesIO(raw)) as frame:
        if frame.width*frame.height>16000000: raise ValueError('Risoluzione eccessiva')
        image=frame.convert('RGB')
    return image,hashlib.sha256(raw).hexdigest()

class Moonraker:
    sensors_cache={}
    metadata_cache={}
    def __init__(self,url): self.url=url.rstrip('/')
    def status(self):
        cached=self.sensors_cache.get(self.url)
        if not cached or time.monotonic()-cached[0]>60:
            try:
                listing=requests.get(self.url+'/printer/objects/list',timeout=(2,3)); listing.raise_for_status()
                sensors=[o for o in listing.json()['result']['objects'] if o.startswith(('filament_switch_sensor ','filament_motion_sensor '))]
                self.sensors_cache[self.url]=(time.monotonic(),sensors)
            except Exception:
                sensors=[]
        else: sensors=cached[1]
        params={'print_stats':'','virtual_sdcard':''}
        params.update({sensor:'' for sensor in sensors})
        r=requests.get(self.url+'/printer/objects/query',params=params,timeout=(2,3))
        r.raise_for_status(); s=r.json()['result']['status']; stats=s['print_stats']
        result={'state':stats['state'],'filename':stats.get('filename',''),
                'progress':s.get('virtual_sdcard',{}).get('progress',0),'fresh':True,
                'filament_used_mm':stats.get('filament_used',0),
                'filament_sensors':[{'name':sensor,'enabled':s.get(sensor,{}).get('enabled'),
                                      'detected':s.get(sensor,{}).get('filament_detected')} for sensor in sensors]}
        filename=result['filename']
        if filename:
            key=(self.url,filename)
            if key not in self.metadata_cache:
                try:
                    metadata=requests.get(self.url+'/server/files/metadata',params={'filename':filename},timeout=(2,3))
                    metadata.raise_for_status(); self.metadata_cache[key]=metadata.json()['result']
                except Exception: pass
            meta=self.metadata_cache.get(key,{})
            for source,dest in [('filament_total','filament_total_mm'),('filament_weight_total','filament_weight_total_g'),('filament_type','filament_type')]:
                if source in meta: result[dest]=meta[source]
        return result
    def pause(self):
        # Re-read immediately before an action; a previous successful poll is insufficient.
        if self.status()['state'] != 'printing': raise RuntimeError('La stampante non sta stampando')
        r=requests.post(self.url+'/printer/print/pause',timeout=(2,4)); r.raise_for_status()
        payload=r.json()
        if 'error' in payload or payload.get('result') != 'ok': raise RuntimeError('Moonraker non ha accettato la pausa')
        for _ in range(3):
            if self.status()['state']=='paused': return True
            time.sleep(0.5)
        raise RuntimeError('Pausa inviata ma non confermata; controllare la stampante')

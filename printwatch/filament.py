"""Spool accounting based on Klipper's reported extruded length, not a physical scale."""
import json
import math
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone

def grams(length_mm, diameter_mm, density):
    return max(0,length_mm)*math.pi*(diameter_mm/2)**2*density/1000

class Spool:
    def __init__(self,path):
        self.path=path; self.lock=threading.RLock(); self.samples=deque()
        self.state=json.loads(path.read_text()) if path.exists() else None

    def save(self):
        temp=self.path.with_suffix('.tmp'); temp.write_text(json.dumps(self.state,indent=2)+'\n')
        os.chmod(temp,0o600); os.replace(temp,self.path)

    def set_remaining(self,remaining,printer):
        if isinstance(remaining,bool) or not isinstance(remaining,(int,float)) or not math.isfinite(remaining) or not 0 <= remaining <= 50000:
            raise ValueError('Inserire da 0 a 50.000 grammi di filamento, esclusa la bobina vuota')
        if not printer.get('fresh') or 'filament_used_mm' not in printer:
            raise ValueError('Serve una lettura aggiornata di Moonraker per impostare la bobina')
        with self.lock:
            self.state={'remaining_g':float(remaining),'last_filename':printer.get('filename',''),
                        'last_used_mm':printer['filament_used_mm'],'set_at':datetime.now(timezone.utc).isoformat(),
                        'observed_consumption_g':0.0,'uncertainty':None}
            self.save()

    def update(self,printer,cfg):
        with self.lock:
            if self.state and printer.get('fresh'):
                used=printer.get('filament_used_mm',0); previous=self.state['last_used_mm']
                if printer.get('filename','') != self.state['last_filename'] or used < previous-1:
                    # New/reset counter: count the current job's already-reported consumption.
                    delta=used
                    self.state['uncertainty']='Contatore cambiato: verificare la bobina se stampe o estrusioni sono avvenute mentre il monitor era spento.'
                else: delta=max(0,used-previous)
                consumed=grams(delta,cfg['diameter_mm'],cfg['density_g_cm3'])
                self.state['remaining_g']-=consumed
                self.state['observed_consumption_g']+=consumed
                self.state['last_used_mm']=used; self.state['last_filename']=printer.get('filename','')
                self.save()
            used=printer.get('filament_used_mm')
            total=printer.get('filament_total_mm')
            weight=printer.get('filament_weight_total_g')
            remaining_mm=max(0,total-used) if used is not None and total is not None else None
            # Use slicer mass/length ratio when present, otherwise configured material density.
            needed=remaining_mm*weight/total if remaining_mm is not None and weight is not None and total and weight>0 else grams(remaining_mm,cfg['diameter_mm'],cfg['density_g_cm3']) if remaining_mm is not None else None
            available=max(0,self.state['remaining_g']) if self.state else None
            now=time.monotonic()
            if printer.get('fresh') and printer.get('state')=='printing' and used is not None:
                if self.samples and (self.samples[-1][2] != printer.get('filename') or used < self.samples[-1][1]): self.samples.clear()
                self.samples.append((now,used,printer.get('filename')))
                while self.samples and now-self.samples[0][0]>300: self.samples.popleft()
            else: self.samples.clear()
            rate=None
            if len(self.samples)>1 and now-self.samples[0][0]>=30:
                rate=grams(used-self.samples[0][1],cfg['diameter_mm'],cfg['density_g_cm3'])/(now-self.samples[0][0])*60
            eta=available/rate if available is not None and rate is not None and rate>0 else None
            return {'consumption_g_min':rate,'spool_minutes_estimate':eta,'sensors':printer.get('filament_sensors',[]),'used_m':used/1000 if used is not None else None,
                    'remaining_print_m':remaining_mm/1000 if remaining_mm is not None else None,
                    'remaining_print_g':needed,'spool_remaining_g':available,
                    'spool_low':available is not None and available < cfg['low_warning_g'],
                    'spool_insufficient':available is not None and needed is not None and available < needed,
                    'stale':not printer.get('fresh',False),'material':printer.get('filament_type'),
                    'settings':cfg,'set_at':self.state['set_at'] if self.state else None,
                    'warning':self.state.get('uncertainty') if self.state else 'Peso bobina non impostato: quantità disponibile sconosciuta.',
                    'limits':'Stima contabile: non misura il peso e non rileva da sola rotture o slittamenti. Le estrusioni manuali fuori stampa non sono conteggiate.'}

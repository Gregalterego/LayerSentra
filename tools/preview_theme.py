"""Read-only local design preview with synthetic data; never connects to a printer."""
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json,mimetypes,time,re
ROOT=Path(__file__).resolve().parents[1]
CAMERA='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 580"><defs><pattern id="grid" width="35" height="35" patternUnits="userSpaceOnUse"><path d="M35 0H0V35" fill="none" stroke="#303030"/></pattern></defs><rect width="1000" height="580" fill="#101010"/><rect width="1000" height="580" fill="url(#grid)"/><g fill="none" stroke="#777" stroke-width="6"><path d="M220 90L800 70 900 430 125 480Z"/><path d="M220 90V380M800 70V320M900 430V510M125 480V540"/></g><path d="M230 350L680 290 785 400 290 465Z" fill="#414141" stroke="#aaa"/><g fill="#c2c0ba" stroke="#f2f0eb"><path d="M425 330L610 310 665 375 470 410Z"/><path d="M425 330V270L610 250V310M425 270L470 350 665 315 610 250M470 350V410M665 315V375"/></g><g fill="#f2f0eb" font-family="monospace" font-size="14"><text x="30" y="38">CAM 01 / ANTEPRIMA GRAFICA</text><text x="30" y="548">DATI DIMOSTRATIVI / NESSUNA STAMPANTE COLLEGATA</text></g><circle cx="963" cy="32" r="6" fill="#ff4b55"/></svg>'''
class Preview(BaseHTTPRequestHandler):
 def do_GET(self):
  path=urlsplit(self.path).path
  data=None;ctype='application/json'
  if path=='/api/config':
   cfg={'cameras':[{'id':'primary','name':'CAM 01 / DEMO','enabled':True}], 'action':'observe','monitoring':True}
   data=json.dumps({'config':cfg,'token':None,'read_only':True,'observation_token':None,'capabilities':{'ptz':{'enabled':False,'reason':'Anteprima: nessun comando motore disponibile.'}}}).encode()
  elif path=='/api/status':
   data=json.dumps({'monitoring':True,'action':'observe','model':'ready','model_error':None,'last_action':None,
    'printer':{'fresh':True,'state':'printing','filename':'ANTEPRIMA · DATI DIMOSTRATIVI','progress':.426},
    'cameras':{'primary':{'state':'ok','analysing':True,'captured_at':time.time(),'inference_ms':48,'confirmation':{}}},
    'filament':{'used_m':128.6,'remaining_print_m':174.2,'remaining_print_g':526.4,'spool_remaining_g':742,'spool_minutes_estimate':283,
      'consumption_g_min':2.6,'spool_insufficient':False,'spool_low':False,'stale':False,
      'warning':'Anteprima grafica: valori dimostrativi.','sensors':[{'name':'Sensore demo','enabled':True,'detected':True}]}}).encode()
  elif path=='/api/events':data=b'[]'
  elif path=='/demo-klipper':
   data=b'<html><body style="background:#101010;color:#f2f0eb;font:16px monospace;padding:24px">ANTEPRIMA GRAFICA / nessun pannello stampante collegato.</body></html>';ctype='text/html'
  elif path=='/api/frame/primary':data=CAMERA.encode();ctype='image/svg+xml'
  else:
   file=ROOT/'static'/('index.html' if path=='/' else path.removeprefix('/static/'))
   if ROOT/'static' not in file.resolve().parents or not file.is_file():self.send_error(404);return
   data=file.read_bytes();ctype=mimetypes.guess_type(file)[0] or 'application/octet-stream'
   if file.name=='app.js':
    data,count=re.subn(rb"function klipperUrl\(\)\{[^\n]*\}",b"function klipperUrl(){return '/demo-klipper';}",data)
    if count!=1:self.send_error(500,'Preview navigation isolation failed');return
  self.send_response(200);self.send_header('Content-Type',ctype+'; charset=utf-8');self.send_header('Content-Security-Policy',"frame-src 'self'; connect-src 'self'; form-action 'none'");self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
 def do_POST(self):self.send_error(405,'Read-only design preview')
 def log_message(self,*args):pass
if __name__=='__main__':
 print('Design preview only: http://127.0.0.1:7135/',flush=True)
 HTTPServer(('127.0.0.1',7135),Preview).serve_forever()

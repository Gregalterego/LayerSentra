import time
import numpy as np
from PIL import Image, ImageDraw
from .config import CATEGORIES

def iou(a,b):
    x=max(a[0],b[0]); y=max(a[1],b[1])
    intersection=max(0,min(a[0]+a[2],b[0]+b[2])-x)*max(0,min(a[1]+a[3],b[1]+b[3])-y)
    union=a[2]*a[3]+b[2]*b[3]-intersection
    return intersection/union if union else 0

def decode(output, width, height, transform, threshold=0.15, nms=0.45):
    a=np.asarray(output)
    if a.ndim != 3 or a.shape[0] != 1: raise ValueError('Output YOLO atteso [1,8,N] o [1,N,8]')
    a=a[0]
    if a.shape[0] == 8: a=a.T
    if a.shape[1] != 8: raise ValueError('Il modello deve avere quattro classi YOLO senza objectness')
    if not np.isfinite(a).all(): raise ValueError('Output modello non finito')
    sx,sy,px,py=transform
    normalized=np.max(np.abs(a[:,:4])) <= 1.5
    detections=[]
    for row in a:
        cls=int(np.argmax(row[4:])); score=float(row[4+cls])
        if score < threshold: continue
        cx,cy,w,h=map(float,row[:4])
        if normalized: cx*=width; w*=width; cy*=height; h*=height
        left=max(0,min(1,((cx-w/2)-px)/sx)); top=max(0,min(1,((cy-h/2)-py)/sy))
        right=max(0,min(1,((cx+w/2)-px)/sx)); bottom=max(0,min(1,((cy+h/2)-py)/sy))
        if right <= left or bottom <= top: continue
        detections.append({'category':CATEGORIES[cls], 'score':round(score,5), 'box':[left,top,right-left,bottom-top]})
    # Suppress duplicates only within the same category.
    kept=[]
    for d in sorted(detections,key=lambda d:d['score'],reverse=True):
        if not any(k['category']==d['category'] and iou(k['box'],d['box']) > nms for k in kept): kept.append(d)
        if len(kept) >= 100: break
    return kept

class Detector:
    def __init__(self,path):
        try:
            from ai_edge_litert.interpreter import Interpreter
        except ImportError:
            try: from tflite_runtime.interpreter import Interpreter
            except ImportError:
                import tensorflow as tf
                Interpreter = tf.lite.Interpreter
        self.runtime=Interpreter(model_path=str(path),num_threads=2)
        self.runtime.allocate_tensors()
        self.input=self.runtime.get_input_details()[0]; self.output=self.runtime.get_output_details()[0]
        shape=self.input['shape']
        if len(shape)!=4 or shape[0]!=1 or shape[3]!=3: raise ValueError('Input atteso [1,H,W,3]')
        self.height=int(shape[1]); self.width=int(shape[2])

    def infer(self, image, camera, config):
        start=time.monotonic()
        image=image.convert('RGB'); w,h=image.size
        masked=image.copy(); draw=ImageDraw.Draw(masked)
        for x,y,rw,rh in camera['masks']: draw.rectangle((int(x*w),int(y*h),int((x+rw)*w),int((y+rh)*h)),fill='black')
        x,y,rw,rh=camera['roi']
        left,top,right,bottom=int(x*w),int(y*h),max(int((x+rw)*w),int(x*w)+1),max(int((y+rh)*h),int(y*h)+1)
        crop=masked.crop((left,top,right,bottom)); cw,ch=crop.size
        if config['resize_mode']=='letterbox':
            scale=min(self.width/cw,self.height/ch)
            nw,nh=max(1,round(cw*scale)),max(1,round(ch*scale))
            px,py=(self.width-nw)//2,(self.height-nh)//2
            resized=Image.new('RGB',(self.width,self.height),(114,114,114))
            resized.paste(crop.resize((nw,nh)),(px,py)); transform=(nw,nh,px,py)
        else:
            resized=crop.resize((self.width,self.height)); transform=(self.width,self.height,0,0)
        values=np.asarray(resized,dtype=np.float32)/255.
        dtype=self.input['dtype']
        if np.issubdtype(dtype,np.integer):
            scale,zero=self.input['quantization']
            if not scale: raise ValueError('Quantizzazione input mancante')
            limits=np.iinfo(dtype); values=np.clip(np.rint(values/scale+zero),limits.min,limits.max).astype(dtype)
        else: values=values.astype(dtype)
        self.runtime.set_tensor(self.input['index'],values[None]); self.runtime.invoke()
        result=self.runtime.get_tensor(self.output['index'])
        if np.issubdtype(result.dtype,np.integer):
            scale,zero=self.output['quantization']
            if not scale: raise ValueError('Quantizzazione output mancante')
            result=(result.astype(np.float32)-zero)*scale
        threshold=min((r['threshold'] for r in config['categories'].values() if r['enabled']),default=1)
        detections=decode(result,self.width,self.height,transform,max(0.05,threshold-0.2),config['nms_iou'])
        mapped=[]
        for d in detections:
            bx,by,bw,bh=d['box']; d['box']=[(left+bx*cw)/w,(top+by*ch)/h,bw*cw/w,bh*ch/h]
            center=(d['box'][0]+d['box'][2]/2,d['box'][1]+d['box'][3]/2)
            if any(mx<=center[0]<=mx+mw and my<=center[1]<=my+mh for mx,my,mw,mh in camera['masks']): continue
            if config['categories'][d['category']]['enabled']: mapped.append(d)
        return mapped,round((time.monotonic()-start)*1000,1)

"""Offline comparison on labelled frames; no printer requests or actions."""
import argparse
import json
import statistics
from pathlib import Path
from PIL import Image
from .config import ROOT, CATEGORIES, load
from .detector import Detector, iou

def evaluate(manifest, config):
    entries=json.loads(manifest.read_text())
    if not isinstance(entries,list) or not entries: raise ValueError('Manifest richiesto come elenco non vuoto')
    detector=Detector(ROOT/config['model_path'])
    counts={c:{'tp':0,'fp':0,'fn':0} for c in CATEGORIES}; latency=[]
    camera=config['cameras'][0]
    for row in entries:
        image_path=(manifest.parent/row['image']).resolve()
        truth=row['annotations']
        for a in truth:
            if a['category'] not in CATEGORIES: raise ValueError('Categoria annotazione sconosciuta')
            from .config import rectangle
            rectangle(a['box'])
        with Image.open(image_path) as image: predictions,ms=detector.infer(image,camera,config)
        latency.append(ms); matched=set()
        for d in sorted(predictions,key=lambda d:d['score'],reverse=True):
            rule=config['categories'][d['category']]
            if d['score']<rule['threshold'] or not rule['minimum_area']<=d['box'][2]*d['box'][3]<=rule['maximum_area']: continue
            candidates=[(iou(d['box'],a['box']),i) for i,a in enumerate(truth) if i not in matched and a['category']==d['category']]
            overlap,index=max(candidates,default=(0,-1))
            if overlap>=.5: matched.add(index); counts[d['category']]['tp']+=1
            else: counts[d['category']]['fp']+=1
        for i,a in enumerate(truth):
            if i not in matched: counts[a['category']]['fn']+=1
    for c in counts.values():
        c['precision']=c['tp']/(c['tp']+c['fp']) if c['tp']+c['fp'] else None
        c['recall']=c['tp']/(c['tp']+c['fn']) if c['tp']+c['fn'] else None
    return {'frames':len(entries),'matching_iou':.5,'categories':counts,
            'mean_inference_ms':round(statistics.mean(latency),1),
            'limits':'Metriche per fotogramma; non misurano ritardo temporale o falsi allarmi per ora. Annotazioni riferite alla stessa ROI/maschere. Modello e dataset non validati da questo programma.'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('manifest',type=Path); p.add_argument('--config',type=Path,default=ROOT/'data/config.json'); p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); result=evaluate(args.manifest,load(args.config)); args.output.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__': main()

"""Raster exports of LayerScan's original vector-like dotted L; requires Pillow."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
theme=json.loads((ROOT/'design/theme.json').read_text())
image=Image.new('RGB',(1024,1024),theme['background']);draw=ImageDraw.Draw(image)
for y,row in enumerate(['100000','100000','100000','100000','100000','100000','111111']):
 for x,on in enumerate(row):
  if on=='1':
   cx,cy=224+x*96,224+y*96
   draw.ellipse((cx-30,cy-30,cx+30,cy+30),fill=theme['text'])
draw.ellipse((774,774,874,874),fill=theme['action'])
app=ROOT/'apps/layerscan_client'
for platform in ('ios','macos'):
 folder=app/platform/'Runner/Assets.xcassets/AppIcon.appiconset'
 for entry in json.loads((folder/'Contents.json').read_text())['images']:
  if not entry.get('filename'):continue
  size=round(float(entry['size'].split('x')[0])*float(entry['scale'].removesuffix('x')))
  image.resize((size,size),Image.Resampling.LANCZOS).save(folder/entry['filename'])
for density,size in {'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}.items():
 image.resize((size,size),Image.Resampling.LANCZOS).save(app/f'android/app/src/main/res/mipmap-{density}/ic_launcher.png')
image.save(app/'windows/runner/resources/app_icon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])

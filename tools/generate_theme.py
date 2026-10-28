"""Generate shared web/native design tokens and an original dotted wordmark."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tokens=json.loads((ROOT/'design/theme.json').read_text())
css='/* Generated from design/theme.json. */\n:root{'+''.join('--'+k+':'+v+';' for k,v in tokens.items() if k not in ('name','radius'))+'--panel:var(--surface);--bg:var(--background);--radius:'+str(tokens['radius'])+'px;}\n'
(ROOT/'static/theme-tokens.css').write_text(css)
dart="// Generated from design/theme.json.\nimport 'package:flutter/material.dart';\nabstract final class LayerScanColors {\n"
for k,v in tokens.items():
 if k not in ('name','radius'):dart+=f'  static const {k} = Color(0xff{v[1:]});\n'
dart+='}\n'
(ROOT/'apps/layerscan_client/lib/theme_tokens.dart').write_text(dart)
# Original 5x7 glyph patterns: no font files or brand assets downloaded.
glyphs={
'L':['10000','10000','10000','10000','10000','10000','11111'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'N':['10001','11001','11001','10101','10011','10011','10001'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'W':['10001','10001','10001','10101','10101','11011','10001'],
'A':['01110','10001','10001','11111','10001','10001','10001'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'H':['10001','10001','10001','11111','10001','10001','10001']}
(ROOT/'design/dot-glyphs.json').write_text(json.dumps(glyphs,indent=2)+'\n')
circles=[]
for i,c in enumerate('LAYERSCAN'):
 for y,row in enumerate(glyphs[c]):
  for x,on in enumerate(row):
   if on=='1':circles.append(f'<circle cx="{i*6+x+0.5}" cy="{y+0.5}" r=".36"/>')
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 53 7" role="img" aria-label="LayerScan"><g fill="'+tokens['text']+'">'+''.join(circles)+'</g></svg>\n'
(ROOT/'static/wordmark.svg').write_text(svg)
brand="""import 'package:flutter/material.dart';
import 'theme_tokens.dart';
class DotWordmark extends StatelessWidget {
  final double width;
  const DotWordmark({super.key, this.width = 230});
  @override
  Widget build(BuildContext context) => Semantics(label: 'LayerScan', image: true,
    child: SizedBox(width: width, height: width * 7 / 53,
      child: CustomPaint(painter: _DotPainter())));
}
class _DotPainter extends CustomPainter {
  static const glyphs = GLYPHS;
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = LayerScanColors.text;
    final scale = size.width / 53;
    for (var i = 0; i < 'LAYERSCAN'.length; i++) {
      final rows = glyphs['LAYERSCAN'[i]]!;
      for (var y = 0; y < rows.length; y++) {
        for (var x = 0; x < rows[y].length; x++) {
          if (rows[y][x] == '1') {
            canvas.drawCircle(Offset((i * 6 + x + .5) * scale, (y + .5) * scale), .36 * scale, paint);
          }
        }
      }
    }
  }
  @override
  bool shouldRepaint(covariant _DotPainter oldDelegate) => false;
}
""".replace('GLYPHS',json.dumps(glyphs))
(ROOT/'apps/layerscan_client/lib/brand.dart').write_text(brand)

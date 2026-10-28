import 'package:flutter/material.dart';
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
  static const glyphs = {"L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"], "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"], "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"], "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"], "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"], "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"], "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"], "N": ["10001", "11001", "11001", "10101", "10011", "10011", "10001"], "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"], "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"], "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"], "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"], "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"]};
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

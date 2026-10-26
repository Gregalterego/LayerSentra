# PrintWatch Dot

Preferred visual direction for this project: an original PrintWatch identity
inspired by the monochrome, dot-matrix and red-accent language the user referenced
at https://it.nothing.tech/ and Nothing OS. Keep future PrintWatch screens consistent
with this direction. Nothing logos, fonts, product photography and assets are not
bundled or copied.

- Charcoal background, neutral grey surfaces, warm white text and red actions.
- Original 5×7 dotted PrintWatch wordmark. Body text stays solid and readable.
- Rounded cards, pill controls, technical monospace labels and tabular numbers.
- Camera first; compact controls remain above or below the video in embedded mode.
- Status and errors use text/icons as well as color. Do not encode state only in a red dot.
- Keep the real printer UI usable; the printer's original Fluidd/Mainsail theme is
  owned by that UI, not overwritten by the companion's page theme.

The shared palette is `design/theme.json`. Run `python tools/generate_theme.py` to
regenerate web tokens, SVG wordmark and native painter/tokens, then `dart format`
on the generated Dart files. `tools/generate_icons.py` exports original launcher
icons with Pillow. There are no remote font, analytics or design-CDN dependencies.

Web styling is in `static/dot-theme.css`. Native styling is in
`apps/printwatch_client/lib/app_theme.dart`. Preview web layout using
`python tools/preview_theme.py` at http://127.0.0.1:7135/ — this preview uses clearly
labelled synthetic data and rejects all commands; it never connects to a printer.

A new source/build does not update an existing server or installed client by itself.
Use the documented host update procedure and install a rebuilt client to see the
new theme in the live installation.

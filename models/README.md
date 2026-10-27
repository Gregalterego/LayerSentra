# Add your own licensed model

No trained model is distributed in this repository.

Place a lawfully obtained, compatible TensorFlow Lite file at `models/model.tflite`.
LayerSentra expects RGB input `[1, height, width, 3]` and YOLO detections `[1, 8, N]`
or `[1, N, 8]`: center x/y, width/height, followed by four class scores in this order:
`spaghetti`, `blob`, `warping`, `crack`. Models with objectness or other class orders
are not supported without an adapter. Float and per-tensor quantized I/O are supported.

The prototype was tested locally with the model from
[CookiezRGood/klipper-print-failure-detection](https://github.com/CookiezRGood/klipper-print-failure-detection),
commit `26c59eb1e0ac37fb1fb04fd72113617d63e1aadf`.
Its SHA-256 was `8e693cd0d21cc147d9e4b1f8b7d3159b8c9c5f1a1fe9692f820f0bcef3e7101b`.
No explicit license was found in that checkout. A public download is not permission
to redistribute the model. Check with its owner and verify model/dataset terms
before using or distributing it. The MIT license in this repository covers the
LayerSentra code, not third-party models or datasets.

Without a model, LayerSentra still provides camera viewing, printer UI access and
filament information; the AI status clearly reports that inference is unavailable.

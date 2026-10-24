# Third-party components and provenance

PrintWatch code is distributed under the MIT license in LICENSE. Installed Python
packages keep their own licenses; requirements files identify the dependencies.
Fluidd/Mainsail are not copied or distributed by PrintWatch: the optional proxy
shows the UI already installed on the user's printer.

The project was inspired by and prototyped against
[CookiezRGood/klipper-print-failure-detection](https://github.com/CookiezRGood/klipper-print-failure-detection).
That project's backend and frontend are not included here. Its trained TFLite model
and training datasets are not redistributed: see models/README.md. An accessible
GitHub repository does not automatically grant model redistribution rights.

FFmpeg, Tailscale, Python, Klipper and Moonraker are separate software. Install/use
those according to their respective terms. Tailscale account features and pricing
are external to this project; PrintWatch does not provide a Tailscale subscription.

"""Compatibility entry point; use layersentra.app for new installations."""
import runpy
if __name__ == "__main__":
    runpy.run_module("layersentra.app", run_name="__main__")

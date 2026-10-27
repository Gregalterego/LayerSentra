"""Compatibility entry point; use layersentra.evaluate for new installations."""
import runpy
if __name__ == "__main__":
    runpy.run_module("layersentra.evaluate", run_name="__main__")

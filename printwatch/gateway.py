"""Compatibility entry point; use layersentra.gateway for new installations."""
import runpy
if __name__ == "__main__":
    runpy.run_module("layersentra.gateway", run_name="__main__")

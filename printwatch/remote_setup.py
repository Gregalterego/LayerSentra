"""Compatibility entry point; use layersentra.remote_setup for new installations."""
import runpy
if __name__ == "__main__":
    runpy.run_module("layersentra.remote_setup", run_name="__main__")

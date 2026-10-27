"""Compatibility entry point; use layersentra.self_host_setup for new installations."""
import runpy
if __name__ == "__main__":
    runpy.run_module("layersentra.self_host_setup", run_name="__main__")

"""Compatibility entry point; use layerscan.remote_setup for new installations."""
import runpy
if __name__ == "__main__":
    runpy.run_module("layerscan.remote_setup", run_name="__main__")

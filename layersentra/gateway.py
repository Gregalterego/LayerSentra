"""Compatibility entry point; use layerscan.gateway for new installations."""
import runpy
if __name__ == "__main__":
    runpy.run_module("layerscan.gateway", run_name="__main__")

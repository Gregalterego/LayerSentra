"""Compatibility entry point; use layerscan.app for new installations."""
import runpy
if __name__ == "__main__":
    runpy.run_module("layerscan.app", run_name="__main__")

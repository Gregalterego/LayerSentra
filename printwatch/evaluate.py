"""Compatibility entry point; use layerscan.evaluate for new installations."""
import runpy
if __name__ == "__main__":
    runpy.run_module("layerscan.evaluate", run_name="__main__")

# Contributing

Use Python 3.12 in a virtual environment and run `python -m unittest discover -s tests -v`.
Tests must not require a live printer, credentials, a camera or distributed model weights.
Add focused tests for parsing, freshness, access control and printer action changes.

Keep machine-specific configuration under `data/` and use synthetic fixtures in tests.
Do not include screenshots, private addresses, credentials, logs, firmware or trained
weights in issues or pull requests. Describe the hardware/firmware family and redact
identifying information in reproduction steps.

Document observed behavior and test scope. Camera reboots, stale frames and printer
state changes must not accidentally arm or trigger automatic actions.

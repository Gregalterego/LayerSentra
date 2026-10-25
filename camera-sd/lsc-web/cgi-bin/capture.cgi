#!/bin/sh
LOCK=/tmp/lsc-capture.lock
if ! mkdir "$LOCK" 2>/dev/null; then
  printf 'Status: 409 Conflict\r\nContent-Type: text/plain\r\n\r\nAcquisizione gia in corso.\n'
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT HUP INT TERM
if [ ! -r /tmp/VideoSubStream0 ] || [ ! -x /tmp/sd/lsc-reader-armv5-v0.3 ]; then
  printf 'Status: 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nVideo non pronto.\n'
  exit 0
fi
printf 'Content-Type: application/octet-stream\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n'
/tmp/sd/lsc-reader-armv5-v0.3 /tmp/VideoSubStream0 20 2>/tmp/lsc-reader-network.log

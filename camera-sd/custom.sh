#!/bin/sh
# Prova video locale: firmware e autenticazione di sistema invariati.
(
  sleep 60
  SD=/tmp/sd
  WEB=/tmp/lsc-web
  grep -q ' /tmp/sd ' /proc/mounts || exit 1
  [ -x "$SD/busybox" ] || exit 1
  [ -d "$SD/lsc-web" ] || exit 1
  mkdir -p "$WEB/cgi-bin" || exit 1
  cp "$SD/lsc-web/index.html" "$WEB/index.html" || exit 1
  cp "$SD/lsc-web/httpd.conf" "$WEB/httpd.conf" || exit 1
  cp "$SD/lsc-web/cgi-bin/capture.cgi" "$WEB/cgi-bin/capture.cgi" || exit 1
  chmod 700 "$WEB/cgi-bin/capture.cgi"
  chmod 600 "$WEB/httpd.conf"
  "$SD/busybox" httpd -p 8080 -h "$WEB" -c "$WEB/httpd.conf" > /tmp/lsc-httpd.log 2>&1
  result=$?
  { echo "httpd_exit=$result"; cat /tmp/lsc-httpd.log; netstat -lnt; } > "$SD/lsc-network-start.txt" 2>&1
  sync
) >/dev/null 2>&1 &
exit 0

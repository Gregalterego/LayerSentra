"""Authenticate a same-machine HTTPS proxy without trusting client identity headers."""
import secrets

PROXY_HEADER = 'X-LayerSentra-Proxy-Token'
LEGACY_PROXY_HEADER = 'X-PrintWatch-Proxy-Token'

def proxy_identity(host, remote, headers, settings, panel=False):
    hostname = settings.get('hostname')
    expected = hostname + (':8443' if panel else '') if hostname else None
    if not panel:
        host = host.removesuffix(':443')
    token = settings.get('proxy_token')
    supplied = headers.get(PROXY_HEADER) or headers.get(LEGACY_PROXY_HEADER, '')
    return bool(expected and host == expected and remote in ('127.0.0.1', '::1')
                and isinstance(token, str) and len(token) >= 32
                and isinstance(supplied, str) and secrets.compare_digest(token, supplied))

"""Private full-UI proxy for Mainsail/Fluidd, including Moonraker WebSockets.
This is a control interface: bind only to loopback and authenticate remote Serve traffic.
"""
import asyncio
import json
from urllib.parse import urlsplit
from aiohttp import web, ClientSession, ClientTimeout, WSMsgType
from .config import ROOT,load
from .access import proxy_identity, PROXY_HEADER, LEGACY_PROXY_HEADER

HOP={'connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailers','transfer-encoding','upgrade','host'}

def authorize(host,remote,headers,mobile):
    hostname=mobile.get('hostname'); local=host in ('127.0.0.1:7128','localhost:7128')
    expected='http://'+host
    if not local:
        if not proxy_identity(host, remote, headers, mobile, panel=True) and (not hostname or host != hostname+':8443' or remote not in ('127.0.0.1','::1')
            or not mobile.get('login') or headers.get('Tailscale-User-Login') != mobile['login']): return False
        expected='https://'+hostname+':8443'
    origin=headers.get('Origin')
    if origin and origin != expected: return False
    # Cross-site form navigations also have to be rejected.
    if headers.get('Sec-Fetch-Site') == 'cross-site' and headers.get('Sec-Fetch-Mode') != 'navigate': return False
    if headers.get('Sec-Fetch-Site') == 'cross-site' and headers.get('Sec-Fetch-Dest') != 'iframe': return False
    return True

async def proxy(request):
    mobile_path=ROOT/'data/mobile-access.json'
    mobile=json.loads(mobile_path.read_text()) if mobile_path.exists() else {}
    if not authorize(request.host,request.remote,request.headers,mobile):
        raise web.HTTPForbidden(text='Accesso Klipper consentito soltanto in locale o tramite accesso remoto autenticato.')
    cfg=load(ROOT/'data/config.json'); target=cfg['moonraker_url'].rstrip('/')
    parsed=urlsplit(target)
    if parsed.path not in ('','/'): raise web.HTTPBadGateway(text='Il proxy richiede l’indirizzo base della stampante senza sottopercorsi.')
    url=target+request.raw_path
    headers={k:v for k,v in request.headers.items() if k.lower() not in HOP and not k.lower().startswith(('tailscale-','x-forwarded-')) and k.lower() not in (PROXY_HEADER.lower(), LEGACY_PROXY_HEADER.lower())}
    headers['Host']=parsed.netloc
    if request.path=='/': headers['Accept-Encoding']='identity'
    if 'Origin' in headers: headers['Origin']=target
    session=request.app['session']
    if request.headers.get('Upgrade','').lower()=='websocket':
        protocols=tuple(x.strip() for x in request.headers.get('Sec-WebSocket-Protocol','').split(',') if x.strip())
        for name in list(headers):
            if name.lower().startswith('sec-websocket-'): headers.pop(name)
        try:
            async with session.ws_connect(url.replace('http','ws',1),headers=headers,protocols=protocols,heartbeat=30,max_msg_size=16*1024*1024) as upstream:
                client=web.WebSocketResponse(protocols=protocols,heartbeat=30,max_msg_size=16*1024*1024)
                await client.prepare(request)
                async def relay(src,dst):
                    try:
                        async for msg in src:
                            if msg.type==WSMsgType.TEXT: await dst.send_str(msg.data)
                            elif msg.type==WSMsgType.BINARY: await dst.send_bytes(msg.data)
                            elif msg.type in (WSMsgType.CLOSE,WSMsgType.CLOSED,WSMsgType.ERROR): break
                    finally: await dst.close()
                tasks=[asyncio.create_task(relay(client,upstream)),asyncio.create_task(relay(upstream,client))]
                try: await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
                finally:
                    for task in tasks: task.cancel()
                    await asyncio.gather(*tasks,return_exceptions=True)
                return client
        except Exception as error: raise web.HTTPBadGateway(text='WebSocket stampante non disponibile: '+str(error))
    try:
        async with session.request(request.method,url,headers=headers,
                data=request.content.iter_chunked(65536) if request.can_read_body else None,allow_redirects=False) as upstream:
            response_headers=upstream.headers.copy()
            for name in list(response_headers):
                if name.lower() in HOP or name.lower() in ('x-frame-options','content-security-policy'):
                    response_headers.popall(name,None)
            parents=['http://127.0.0.1:7127','http://localhost:7127']
            if mobile.get('hostname'): parents.append('https://'+mobile['hostname'])
            response_headers['Content-Security-Policy']="frame-ancestors "+' '.join(parents)
            location=response_headers.get('Location')
            if location and location.startswith(target):
                scheme='http' if request.host.startswith(('127.0.0.1:','localhost:')) else 'https'
                response_headers['Location']=scheme+'://'+request.host+location[len(target):]
            if request.path=='/' and request.method=='GET' and 'text/html' in upstream.headers.get('Content-Type',''):
                html=await upstream.read()
                style=b'<style>iframe.camera-image[src*="embed=camera"]{width:100%!important;display:block;max-width:100%;height:auto!important;aspect-ratio:4/3;min-height:320px;}</style>'
                html=html.replace(b'</head>',style+b'</head>',1)
                response_headers.popall('Content-Length',None)
                response_headers.popall('Content-Encoding',None)
                response_headers.popall('ETag',None)
                return web.Response(body=html,status=upstream.status,headers=response_headers)
            response=web.StreamResponse(status=upstream.status,headers=response_headers)
            await response.prepare(request)
            async for chunk in upstream.content.iter_chunked(65536): await response.write(chunk)
            await response.write_eof(); return response
    except (web.HTTPException,ConnectionResetError): raise
    except Exception as error: raise web.HTTPBadGateway(text='Stampante non disponibile: '+str(error))

async def session_context(app):
    async with ClientSession(timeout=ClientTimeout(total=None,sock_connect=5,sock_read=90),auto_decompress=False) as session:
        app['session']=session; yield

def main():
    app=web.Application(client_max_size=100*1024*1024)
    app.cleanup_ctx.append(session_context); app.router.add_route('*','/{path:.*}',proxy)
    web.run_app(app,host='127.0.0.1',port=7128,access_log=None,print=None)

if __name__=='__main__': main()

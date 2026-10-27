'use strict';
const el = id => document.getElementById(id);
const urls = new Map();
let csrf = '', busy = false, holding = null, state = 'unknown', fresh = false, canResume = false;
async function api(path, body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const options = {credentials:'same-origin',cache:'no-store',signal:controller.signal};
    if (body !== undefined) Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json','X-Guest-CSRF':csrf},body:JSON.stringify(body)});
    const response = await fetch(path,options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Collegamento non disponibile');
    return data;
  } finally { clearTimeout(timeout); }
}
function clearFrame(cid, message) {
  const image = el('camera-'+cid); image.hidden = true; image.removeAttribute('src');
  el('offline-'+cid).hidden = false; el('offline-'+cid).textContent = message;
  if (urls.has(cid)) URL.revokeObjectURL(urls.get(cid));
  urls.delete(cid);
}
function permitted(action) { return fresh && (action !== 'resume' || canResume) && state === (action === 'pause' ? 'printing' : 'paused'); }
function buttons() {
  for (const action of ['pause','resume']) el(action).disabled = busy || !permitted(action) || (holding !== null && holding.action !== action);
}
function resetButton(button) {
  button.style.setProperty('--hold','0%'); button.classList.remove('holding');
  button.querySelector('span').textContent = button.id === 'pause' ? 'PAUSA STAMPA' : 'RIPRENDI STAMPA';
}
function cancelHold(message) {
  const h = holding; if (!h) return;
  holding = null; cancelAnimationFrame(h.frame); resetButton(h.button);
  if (h.token) api('/api/hold/cancel',{hold_token:h.token}).catch(() => {});
  if (message) el('message').textContent = message;
  buttons();
}
async function camera(cid, ready) {
  if (!ready) { clearFrame(cid,'Telecamera non disponibile'); return; }
  const controller = new AbortController(), timer = setTimeout(() => controller.abort(),8000);
  try {
    const response = await fetch('/api/frame/'+cid,{cache:'no-store',credentials:'same-origin',signal:controller.signal});
    if (!response.ok) throw new Error('Video non aggiornato');
    const url = URL.createObjectURL(await response.blob());
    if (urls.has(cid)) URL.revokeObjectURL(urls.get(cid));
    urls.set(cid,url); el('camera-'+cid).src = url;
    el('camera-'+cid).hidden = false; el('offline-'+cid).hidden = true;
  } catch (_) { clearFrame(cid,'Video non aggiornato o non disponibile'); }
  finally { clearTimeout(timer); }
}
async function update() {
  try {
    const data = await api('/api/status'); csrf = data.csrf; state = data.state; canResume = data.can_resume === true; fresh = data.printer_ready === true;
    el('status').textContent = 'Stato stampa: '+({printing:'in stampa',paused:'in pausa',standby:'in attesa',complete:'completata',cancelled:'annullata',error:'errore'}[state] || 'non noto');
    if (holding && !permitted(holding.action)) cancelHold('Stato cambiato: pressione annullata.');
    buttons();
    await Promise.all(['primary','secondary'].map(cid => camera(cid,(data.cameras || []).find(c => c.id === cid)?.ready === true)));
  } catch (error) {
    fresh = false; cancelHold('Collegamento interrotto: pressione annullata.'); buttons();
    el('status').textContent = error.message;
    for (const cid of ['primary','secondary']) clearFrame(cid,'Collegamento non disponibile');
  }
}
async function execute(h) {
  if (holding !== h || !permitted(h.action)) { cancelHold('Pressione annullata.'); return; }
  holding = null; busy = true; resetButton(h.button); buttons();
  el('message').textContent = h.action === 'pause' ? 'Richiesta pausa in corso…' : 'Richiesta ripresa in corso…';
  try {
    await api('/api/'+h.action,{hold_token:h.token});
    el('message').textContent = h.action === 'pause' ? 'Stampante in pausa: confermato.' : 'Stampa ripresa: confermato.';
  } catch (error) { el('message').textContent = error.message; }
  finally { busy = false; await update(); }
}
async function begin(button) {
  if (holding || busy || button.disabled || !permitted(button.id)) return;
  const h = {button,action:button.id,token:null,frame:0}; holding = h; buttons();
  el('message').textContent = 'Continua a tenere premuto. Rilascia per annullare.';
  try {
    const grant = await api('/api/hold',{action:h.action}); h.token = grant.hold_token;
    if (holding !== h) { api('/api/hold/cancel',{hold_token:h.token}).catch(() => {}); return; }
    h.started = performance.now(); button.classList.add('holding');
    function tick() {
      if (holding !== h) return;
      const elapsed = performance.now()-h.started;
      button.style.setProperty('--hold',Math.min(100,elapsed/50)+'%');
      button.querySelector('span').textContent = (h.action === 'pause' ? 'PAUSA' : 'RIPRENDI')+' · '+Math.max(0,Math.ceil((5000-elapsed)/1000))+' s';
      if (elapsed >= 5000) execute(h); else h.frame = requestAnimationFrame(tick);
    }
    tick();
  } catch (error) { if (holding === h) { cancelHold(); el('message').textContent = error.message; } }
}
for (const action of ['pause','resume']) {
  const button = el(action);
  button.addEventListener('pointerdown',event => {
    if (event.button !== 0 || !event.isPrimary || button.disabled) return;
    event.preventDefault(); button.focus({preventScroll:true}); button.setPointerCapture(event.pointerId); begin(button);
  });
  for (const name of ['pointerup','pointercancel','lostpointercapture']) button.addEventListener(name,() => {
    if (holding?.button === button) cancelHold('Pressione annullata: tieni premuto per 5 secondi.');
  });
  button.addEventListener('pointermove',event => {
    const r = button.getBoundingClientRect();
    if (holding?.button === button && (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom)) cancelHold('Pressione annullata.');
  });
  button.addEventListener('keydown',event => {
    if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); if (!event.repeat) begin(button); }
  });
  button.addEventListener('keyup',event => {
    if ((event.key === ' ' || event.key === 'Enter') && holding?.button === button) cancelHold('Pressione annullata.');
  });
  button.addEventListener('blur',() => { if (holding?.button === button) cancelHold('Pressione annullata.'); });
  button.addEventListener('click',event => event.preventDefault());
  button.addEventListener('contextmenu',event => event.preventDefault());
}
window.addEventListener('blur',() => cancelHold('Pressione annullata.'));
window.addEventListener('pagehide',() => cancelHold());
document.addEventListener('visibilitychange',() => { if (document.hidden) cancelHold(); });
async function start() {
  const token = new URLSearchParams(location.hash.slice(1)).get('invite'); history.replaceState(null,'',location.pathname);
  if (token) { try { await api('/session',{token}); } catch (error) { el('status').textContent = error.message; return; } }
  async function poll() { await update(); setTimeout(poll,1500); }
  poll();
}
start();

'use strict';
const el = id => document.getElementById(id);
let csrf = '', busy = false, currentURL = null;
const directions = [...document.querySelectorAll('[data-direction]')];
async function api(path, body) {
  const options = {credentials: 'same-origin', cache: 'no-store'};
  if (body !== undefined) Object.assign(options, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Guest-CSRF': csrf}, body: JSON.stringify(body)});
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Collegamento non disponibile');
  return data;
}
function clearFrame() {
  el('camera').hidden = true; el('offline').hidden = false;
  el('camera').removeAttribute('src');
  if (currentURL) URL.revokeObjectURL(currentURL);
  currentURL = null;
}
async function update() {
  try {
    const state = await api('/api/status'); csrf = state.csrf;
    el('status').textContent = 'Stato stampa: ' + ({printing:'in stampa',paused:'in pausa',standby:'in attesa',complete:'completata',error:'errore'}[state.state] || 'non noto');
    el('pause').disabled = busy || state.state !== 'printing';
    directions.forEach(button => button.disabled = !state.ptz || busy);
    el('ptzInfo').textContent = state.ptz ? 'Movimento a piccoli impulsi · Stop arresta la telecamera.' : 'Movimento non disponibile: serve un bridge PTZ collaudato.';
    if (!state.camera_ready) { clearFrame(); return; }
    const response = await fetch('/api/frame', {cache:'no-store', credentials:'same-origin'});
    if (!response.ok) throw new Error('Video non disponibile o immagine non aggiornata');
    const url = URL.createObjectURL(await response.blob());
    if (currentURL) URL.revokeObjectURL(currentURL);
    currentURL = url; el('camera').src = url; el('camera').hidden = false; el('offline').hidden = true;
  } catch (error) {
    el('status').textContent = error.message; el('pause').disabled = true;
    directions.forEach(button => button.disabled = true); clearFrame();
  }
}
async function action(path, body) {
  if (busy) return;
  busy = true; el('pause').disabled = true; directions.forEach(button => button.disabled = true);
  el('message').textContent = path.endsWith('pause') ? 'Richiesta pausa in corso…' : 'Comando telecamera in corso…';
  try { await api(path, body); el('message').textContent = path.endsWith('pause') ? 'Stampante in pausa: confermato.' : 'Comando telecamera accettato.'; }
  catch(error) { el('message').textContent = error.message; }
  finally { busy = false; }
}
el('pause').addEventListener('click', () => action('/api/pause', {}));
directions.forEach(button => button.addEventListener('click', () => action('/api/ptz', {direction:button.dataset.direction})));
async function start() {
  const token = new URLSearchParams(location.hash.slice(1)).get('invite');
  history.replaceState(null, '', location.pathname);
  if (token) {
    try { await api('/session', {token}); }
    catch(error) { el('status').textContent = error.message; return; }
  }
  // Sequential polling avoids overlapping requests and discards images on failure.
  async function poll() { await update(); setTimeout(poll, 1500); }
  poll();
}
start();

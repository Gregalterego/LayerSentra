# Server proprio, VPS o dominio personale

LayerScan può essere eseguito su un computer sempre acceso, un mini PC o un server
proprio. Un dominio è l'indirizzo del servizio: non esegue il programma.
GitHub Pages, un link condiviso e un normale hosting di sole pagine statiche non
possono ospitare Python, il modello AI e i collegamenti in tempo reale di Klipper.
Un hosting condiviso va bene soltanto se permette processi Python persistenti,
connessioni in uscita alla stampante, WebSocket e un proxy HTTPS configurabile.

## Scegli dove eseguire il progetto

| Destinazione | Requisiti |
| --- | --- |
| Mac desktop o mini PC in azienda | Sempre acceso, stampante e camera raggiungibili; Tailscale è la strada privata più semplice. |
| Server Linux in rete locale | Python 3.12, runtime compatibile, servizio systemd opzionale. |
| VPS o server remoto | VPN verso la rete della stampante e telecamera; traffico video e costi del provider da valutare. |
| Dominio personale | DNS verso il server, HTTPS e autenticazione; il dominio da solo non basta. |

Non aprire Moonraker o la telecamera direttamente su Internet. Un server remoto
raggiunge gli indirizzi privati soltanto se dispone di una route VPN: copiare un
indirizzo LAN su un VPS non crea quella connessione.

## 1. Installa e configura il programma sul server

Scarica il repository da GitHub. Nella sua cartella, con Python 3.12 installato:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m layerscan.app
```

Usa `requirements-intel.txt` su Mac Intel. La disponibilità delle librerie AI dipende
da sistema e architettura; Linux non è ancora verificato su ogni hardware.
Aggiungi il tuo modello autorizzato in `models/model.tflite`.

Se il server è remoto, apri il pannello locale con un tunnel SSH dal tuo computer:

```sh
ssh -L 7127:127.0.0.1:7127 -L 7128:127.0.0.1:7128 utente@server
```

Visita `http://127.0.0.1:7127` e configura gli indirizzi della stampante e della
camera **raggiungibili dal server**. Verifica video, stato e modello. Chiudi la prima
istanza prima di attivare un servizio. Avvia con `--observe` per osservazione automatica.

## 2. Accesso con un dominio proprio

Questa modalità usa **Caddy 2.8 o successivo sullo stesso server di LayerScan**.
Installa Caddy dalla [documentazione ufficiale](https://caddyserver.com/docs/install).
È un'alternativa a Tailscale Serve: non usare entrambi sulle stesse porte.
Il generatore conserva le configurazioni remote preesistenti e rifiuta di sovrascriverle.

Occorrono un dominio sotto il tuo controllo, DNS corretto e accesso al server sulle
porte 80/443 per HTTPS e 8443 per il pannello stampante. Un eventuale record AAAA deve
puntare anch'esso al server corretto. Non aprire le porte applicative 7127/7128.

Genera una password robusta con il comando interattivo di Caddy e crea i file locali:

```sh
.venv/bin/python -m layerscan.self_host_setup \
  --hostname stampa.example.org \
  --user operatore \
  --password-hash "$(caddy hash-password)"
```

Il dominio è un esempio: sostituiscilo con il tuo. La password viene richiesta da
Caddy; LayerScan riceve soltanto l'hash. Il comando scrive `data/mobile-access.json`
e `data/Caddyfile` con permessi privati, senza modificare DNS, firewall o servizi.
Non condividere questi file: contengono il segreto tra proxy e applicazione.

Controlla la configurazione generata:

```sh
caddy validate --config data/Caddyfile --adapter caddyfile
```

Su un server Linux dedicato, dopo aver verificato che non sostituisca altri siti,
installa il file nella configurazione del tuo servizio Caddy. Per una nuova
installazione con gruppo `caddy`:

```sh
sudo install -o root -g caddy -m 640 data/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Se Caddy ospita già altri siti, integra i due blocchi nel file esistente invece di
sostituirlo. Riavvia LayerScan affinché legga la nuova identità remota.

Gli indirizzi risultanti sono:

- `https://stampa.example.org/`: video, AI, filamento e controllo della sola osservazione.
- `https://stampa.example.org:8443/`: pannello completo e comandi reali alla stampante.
- `https://stampa.example.org/?embed=camera`: vista grande da aggiungere a Fluidd.

Entrambi gli accessi richiedono utente e password. Apri una prima volta il pannello
sulla porta 8443 in una scheda separata per autenticarti prima di incorporarlo.
L'accesso al pannello completo consente a chi possiede le credenziali di controllare
la stampante. Le app telefono devono supportare HTTPS, porta personalizzata e
HTTP Basic Auth; in caso contrario usa il browser o la modalità privata Tailscale.

Caddy autentica l'utente e sostituisce l'header segreto prima di inoltrare la richiesta.
LayerScan accetta tale identità soltanto da loopback, sul dominio atteso; i segreti
non sono inviati alla stampante. Un proxy su un altro computer/container non è
supportato da questa configurazione. Non pubblicare direttamente il server Flask.

## 3. Avvio automatico Linux

Il file [deploy/layerscan.service](deploy/layerscan.service) è un esempio per
un'installazione in `/opt/layerscan` con account dedicato `layerscan`.
Crea prima tale account e prepara la cartella con proprietà e permessi adatti.
L'utente del servizio deve leggere codice/modello e scrivere in `data/`; non deve
avere privilegi amministrativi. Non usare una cartella home con questo esempio,
che protegge le home tramite systemd.

```sh
sudo install -m 644 deploy/layerscan.service /etc/systemd/system/layerscan.service
sudo systemctl daemon-reload
sudo systemctl enable --now layerscan
sudo systemctl status layerscan
sudo journalctl -u layerscan -n 80 --no-pager
```

Adatta utente e percorsi prima di installarlo. Il servizio parte in osservazione e
viene riavviato in caso di errore. Per fermarlo: `sudo systemctl stop layerscan`.
Su Mac usa `enable-autostart.command`: impedisce lo stop per inattività quando
alimentato, ma richiede l'accesso dell'utente dopo un riavvio.

## 4. Verifiche prima di affidarsi al server

- Modello pronto e inferenza verificata su un fotogramma reale.
- Video recente e stampante raggiungibile dal server.
- Accessi senza credenziali rifiutati su entrambi gli indirizzi.
- Comandi, aggiornamenti in tempo reale e WebSocket verificati senza avviare stampe di prova indesiderate.
- Computer precedente spento o applicazione arrestata: il nuovo server continua a funzionare.
- Riavvio del server verificato, con eventuale sblocco necessario.
- Sensore filamento e grammi sulla bobina verificati separatamente: il software non li abilita né li misura da solo.

La modalità con dominio include test automatici dell'autorizzazione e generazione
della configurazione. Non costituisce una certificazione di un'installazione pubblica:
DNS, certificati, autenticazione e riavvio vanno verificati sul proprio server.

### Controlli remoti nel server 0.4.0

Il pannello remoto permette di avviare e fermare l’osservazione e, soltanto con un
bridge configurato, inviare brevi impulsi PTZ. Queste operazioni usano token distinti
e gli stessi controlli di identità e origine. La modifica generale dei parametri
rimane bloccata. Avviare o fermare l’analisi forza sempre la sola osservazione.

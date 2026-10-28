# Monitor locale e integrazione Fluidd

## Installazione

1. Scaricare una release del repository e leggere il suo README, i requisiti del modello e le dipendenze della piattaforma.
2. Estrarre il progetto in una cartella dedicata. Conservare separatamente eventuali dati di una precedente installazione.
3. Installare le dipendenze nell’ambiente isolato previsto dalla release. Dove forniti, usare gli script `install.command` e `start.command`; i nomi possono variare nelle versioni successive.
4. Avviare il server e aprire la sua interfaccia locale. Nel percorso descritto il monitor usa la porta 7127 e un gateway separato la 7128.
5. Configurare privatamente l’indirizzo Moonraker della propria stampante, per esempio `http://printer.example.invalid`, e l’URL che restituisce un’immagine della camera.
6. Iniziare in sola osservazione. Controllare modello, collegamento, fotogrammi e stato stampante prima di pensare a qualsiasi azione automatica.

Non copiare una configurazione completa da un altro impianto: potrebbe contenere URL privati, maschere errate o impostazioni che comandano un’altra stampante.

## Verifica della sorgente Moonraker

Sul proprio impianto verificare richieste in sola lettura a:

| Endpoint Moonraker | Scopo |
|---|---|
| `/server/info` | Collegamento a Klipper e componenti |
| `/printer/objects/list` | Oggetti e sensori effettivamente esposti |
| `/printer/objects/query?print_stats&virtual_sdcard` | Stato, file, consumo e avanzamento |
| `/server/files/metadata?filename=...` | Metadati del file di stampa |

Usare l’autenticazione prevista dalla propria installazione. Non aggirarla con intestazioni che simulano un altro utente. Il nome del file deve essere codificato come parametro URL. I dati dipendono dalla versione di Moonraker, dal G-code e dall’estrazione dei metadati.

Letture significative: `print_stats.state`, `print_stats.filename`, `print_stats.filament_used`, `virtual_sdcard.progress`; quando presenti, `filament_total`, `filament_weight_total` e `filament_type` nei metadati. I sensori vanno individuati dall’elenco oggetti, non inventando un nome fisso.

## Camera nel monitor

Una sorgente snapshot deve restituire una singola immagine valida, non una pagina di login o un flusso binario proprietario. RTSP richiede un decoder sul server: il browser non è un client RTSP diretto.

Nel monitor abilitare la seconda camera soltanto dopo una prova con immagine recente. Il percorso LSC usa un bridge interno che espone `/api/lsc/snapshot`; `/api/lsc/status` permette di controllare disponibilità e anzianità del fotogramma. `/api/frame/secondary` è il fotogramma gestito dal monitor: può non essere disponibile se è scaduto o se la camera non è stata acquisita.

## Vista in Fluidd

1. Aprire le impostazioni telecamere della propria versione di Fluidd.
2. Conservare la camera originale e aggiungere, se supportato, una vista pagina/iframe del monitor.
3. Usare un URL raggiungibile dal browser che aprirà Fluidd, per esempio `https://monitor.example.invalid/?embed=camera`.
4. Verificare video, popup «Dati e filamento», schermo intero e comandi AI.
5. Verificare anche da telefono: `localhost` del telefono non indica il server.

Le versioni di Fluidd possono memorizzare le camere in modi diversi. Una lista vuota da un’API webcam di Moonraker non dimostra che Fluidd non abbia camere nel proprio database. Non modificare il database alla cieca e non creare duplicati se la voce è già presente.

## Avvio continuativo

Configurare l’avvio automatico con il meccanismo fornito dalla release. Su macOS un LaunchAgent dipende normalmente dalla sessione utente: fare una prova dopo logout/login e riavvio. Verificare il percorso FFmpeg nell’ambiente del servizio, che può essere diverso da quello del terminale. Il servizio deve restare raggiungibile quando lo schermo si spegne; lo stop del computer interrompe elaborazione e avvisi.

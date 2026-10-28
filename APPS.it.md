# LayerScan per iPhone, Android, Mac e Windows

Il client nativo è sviluppato con Flutter. La versione 0.6.0 usa il tema LayerScan Dot,
con palette monocromatica, accenti rossi e marchio originale a punti. Vedi [DESIGN.md](DESIGN.md). Si collega al tuo server LayerScan,
mostra immagini, stato stampa e filamento, e incorpora il pannello completo Klipper.
L'analisi AI continua sul server: il telefono o il portatile possono chiudere l'app.

## Nuovi pacchetti LayerScan

Le nuove compilazioni del workflow [Native apps](https://github.com/Gregalterego/LayerScan/actions/workflows/apps.yml)
producono i pacchetti elencati sotto. Controllare l’esito del workflow prima di scaricarli. La compilazione non equivale a un collaudo fisico di ogni dispositivo:
la prova reale dell'interfaccia è stata eseguita su Mac, collegato a un server attivo.
I pacchetti delle compilazioni precedenti mantengono il nome storico; scaricare una compilazione successiva alla rinomina per ottenere LayerScan. Nessun pacchetto è stato pubblicato negli store.

| Piattaforma | Pacchetto | Come usarlo |
| --- | --- | --- |
| Android | `LayerScan-Android-test.zip` | Estrarre l’APK di debug per test; non è una release Google Play. |
| Windows | `LayerScan-Windows-test.zip` | Estrarre tutta la cartella e aprire `layerscan.exe`. Conservare DLL e `data` accanto all'eseguibile. Richiede Microsoft WebView2. |
| Mac | `LayerScan-macOS-test.zip` | Estrarre `LayerScan.app`. Build di prova senza firma Developer ID e notarizzazione; macOS può richiedere una distribuzione firmata prima di consentirne l'apertura. |
| iPhone | `LayerScan-iOS-unsigned.zip` | Bundle senza firma per sviluppatori: non si installa direttamente su un normale iPhone. Serve firmare dal progetto Xcode con il proprio account autorizzato, oppure predisporre TestFlight/App Store. |

Non sono inclusi certificati, chiavi di firma o account sviluppatore. Il pacchetto
Android usa una chiave di debug del sistema di compilazione: gli aggiornamenti di
prova generati in ambienti diversi possono richiedere una nuova installazione.
Per distribuire una versione finale Android occorre una propria chiave stabile;
per Apple firma e notarizzazione/distribuzione vanno configurate con il proprio account.

## Primo collegamento

1. Verifica che il server LayerScan sia acceso e raggiungibile.
2. Se usi un indirizzo privato Tailscale, collega anche il dispositivo alla tua rete Tailscale.
3. Inserisci nell'app l'URL HTTPS della dashboard, senza password nell'indirizzo.
4. Il pannello Klipper usa normalmente lo stesso nome con porta 8443. Puoi indicare un URL HTTPS diverso nel secondo campo.
5. Con un dominio protetto da password, l'app richiede le credenziali per la sessione. Il pannello Klipper può richiedere un accesso separato.

L'app salva soltanto gli indirizzi nei preferiti locali. Non viene fornito alcun
indirizzo di una stampante reale. Le credenziali inserite dal client non vengono
salvate nelle preferenze; la vista incorporata richiede autenticazione non permanente.
Non è prevista una funzione push o di analisi in background sul telefono.

## Avvia e ferma analisi AI

Il comando è visibile nella barra in alto dell'app e nel pannello web, anche nella
camera incorporata in Klipper. Richiede **server 0.4.0**: un server precedente può
fornire il video ma non accettare il nuovo comando.

Avviare o fermare l'analisi forza la modalità di sola osservazione. Non abilita la
pausa automatica della stampante. L'analisi effettiva richiede modello pronto,
monitoraggio abilitato, camera disponibile e una stampa attiva; in standby resta
in attesa. Il servizio avviato con `--observe` riabilita l'osservazione al successivo
avvio del processo: il comando Ferma non disattiva l'avvio automatico del servizio.

Per una precedente installazione Mac in `~/Applications/LayerScan` (o nel percorso storico `~/Applications/PrintWatch`), estrai il nuovo
sorgente in una cartella separata sullo stesso server ed esegui `update-macos.command`.
Lo script crea un backup del codice, conserva dati e modello e si ferma se rileva
una stampa attiva o in pausa. Non aggiorna il computer remoto soltanto perché
scarichi o installi l'app sul telefono.

## Movimento LSC

Le frecce sono predisposte nell'app e nel pannello web. Restano disabilitate senza
un bridge PTZ esplicitamente configurato e verificato: il video da solo non prova
la disponibilità dei comandi motori. Non è incluso un driver PTZ diretto della LSC.
Vedi [requisiti e configurazione](PTZ.it.md).

## Codice e verifiche

Il progetto è in [apps/layerscan_client](apps/layerscan_client). Sono stati eseguiti
analisi Flutter senza segnalazioni, due test del client e 58 test del server.
Le build native sono prodotte dai sistemi GitHub per le rispettive piattaforme.
La firma pubblica e le prove su iPhone, Android e Windows reali restano separate
dalle compilazioni e dalla prova Mac.

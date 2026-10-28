# Telecamera LSC / Anyka: dall’analisi al video

## Analisi statica prima delle modifiche

1. Conservare privatamente una copia originale dei file acquisiti e calcolarne SHA-256.
2. Identificare formato ELF, architettura, ABI e dipendenze con strumenti di analisi statica. Non avviare o emulare l’eseguibile originale per questa procedura.
3. Esaminare script di avvio e richiami ai servizi, distinguendo una stringa o un richiamo dalla presenza effettiva del servizio.
4. Se si estraggono filesystem da copie autorizzate, lavorare in una cartella nuova e non materializzare nodi speciali o link non controllati.
5. Corroborare le ipotesi con inventari raccolti legittimamente dal dispositivo: processi, file aperti, dimensioni dei buffer e porte in ascolto.

La presenza di simboli RTSP non dimostra che un server sia in ascolto. Un richiamo a uno script ONVIF non dimostra che lo script o il servizio siano presenti. Non introdurre credenziali predefinite indovinate o tentativi ripetuti di accesso.

## Risultato specifico della famiglia studiata

Sono stati individuati buffer prodotti dal processo originale:

| Percorso sulla telecamera | Contenuto osservato nel caso studiato |
|---|---|
| `/tmp/VideoSubStream0` | H.264, 640×360 |
| `/tmp/VideoMainStream0` | H.265, 2304×1296 |

Per il secondario è stata ricostruita una struttura circolare con prefisso metadati 0x6000, area dati 0x40000 e intestazioni record di 36 byte. Questi numeri sono **specifici della revisione studiata**: non sono un protocollo universale Anyka.

Il lettore sperimentale apre in sola lettura, confronta copie dei dati e attende un keyframe dopo una discontinuità. Non modifica mutex, non registra consumatori nel processo e non riapre il sensore. Rimangono possibili corse con il produttore: due copie uguali non sono una garanzia di atomicità.

## Formato di trasporto LSC1

| Campo | Dimensione | Significato |
|---|---:|---|
| Magic | 4 byte | `LSC1` |
| Timestamp | 8 byte, big-endian | Timestamp sorgente, interpretato in millisecondi |
| Lunghezza | 4 byte, big-endian | Dimensione del payload |
| Payload | Variabile | H.264 Annex B |

LSC1 è un contenitore del prototipo, non un formato ufficiale del produttore. Una risposta LSC1 non è direttamente un’immagine JPEG né un URL RTSP. Il bridge deve validare lunghezze, gestire i timestamp e inviare il payload a FFmpeg.

## Prima prova limitata su microSD

Prerequisito: bootstrap già funzionante per la propria telecamera.

1. Spegnere la telecamera e fare un backup della scheda e degli script esistenti.
2. Compilare o procurarsi legittimamente un lettore compatibile. Il target della prova era ARMv5 soft-float; una compilazione statica riuscita non prova compatibilità runtime.
3. Predisporre un test di durata limitata che salvi output e log solo sulla SD, senza cambiare flash, servizi originali o password di sistema.
4. Avviare la camera, attendere il termine, spegnerla e recuperare i risultati.
5. Sul computer verificare integrità dei record, timestamp, decodifica FFmpeg, log e stato del processo originale. Non eseguire localmente i programmi proprietari ARM.

Nella prova v0.3 sono stati decodificati 201 fotogrammi H.264. È comparsa anche una discontinuità di circa 2,4 secondi: il risultato dimostra che il percorso può funzionare sul dispositivo studiato, non uno streaming perfetto o una compatibilità generale.

## Servizio HTTP sulla scheda

Dopo la prova del lettore, la soluzione installata usa:

- `custom.sh` richiamato dal bootstrap conosciuto;
- BusyBox compatibile e lettore v0.3 sulla SD;
- webroot temporaneo sotto `/tmp`, porta HTTP 8080;
- `capture.cgi` che esegue acquisizioni limitate, con un solo client alla volta;
- autenticazione HTTP Basic configurata privatamente;
- bridge persistente sul computer, che riconnette le richieste e produce JPEG recenti.

Una richiesta dura nominalmente 20 secondi; il buffer può includere fotogrammi precedenti all’apertura. Non stimare durata o latenza contando soltanto i frame. Controllare l’età delle immagini e azzerare le conferme AI quando mancano immagini valide.

Il file privato `httpd.conf` deve proteggere l’intero webroot. Non distribuire un esempio con una password realmente utilizzabile. Il file di configurazione del bridge deve contenere separatamente URL, username, password e percorso FFmpeg, con permessi restrittivi. HTTP Basic non cifra il traffico: usarlo solo su una rete locale fidata o un collegamento adeguatamente protetto, senza esporre la porta camera a Internet.

Lo script corrente della soluzione video copia soltanto i file che conosce. Un nuovo CGI copiato sulla SD non diventa automaticamente accessibile: anche lo script di avvio deve pubblicarlo. La scheda deve restare inserita durante il funzionamento.

## RTSP e coesistenza con l’app

Il server RTSP realizzato durante le prove era un **replay di un file sul computer**, non un server live installato nella camera. La soluzione video effettivamente provata usa HTTP/LSC1 e FFmpeg. Non pubblicizzare un RTSP nativo abilitato senza una prova di rete riuscita.

Leggere il buffer già prodotto riduce la necessità di contendere il sensore con l’app originale. Non prova però compatibilità completa con live view, registrazione, notifiche e aggiornamenti Tuya. Serve una prova prolungata di tutte le funzioni interessate se la coesistenza è un requisito.

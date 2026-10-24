# PrintWatch — guida rapida

Software gratuito e open source con licenza MIT per monitorare stampanti Klipper
con immagini, AI locale, pannello Fluidd/Mainsail e stima del filamento.

## Avvio

Serve Python 3.12. Su Mac apri `install.command`, poi `start.command`.
In alternativa segui i comandi nel [README principale](README.md).
Apri **http://127.0.0.1:7127** e, in **Parametri**, inserisci l'indirizzo della tua
stampante/Moonraker e l'URL snapshot della tua telecamera. I valori iniziali sono
segnaposto locali: non è inclusa la configurazione di una stampante reale.

Per usare l’AI devi aggiungere un modello TFLite compatibile in `models/model.tflite`.
Il modello non è distribuito: [formato, provenienza e diritti](models/README.md).
Senza modello restano disponibili immagini, filamento e accesso al pannello stampante.

La modalità iniziale è sola osservazione, con analisi ferma. Il Mac deve restare
acceso e raggiungere la stampante. L'app non usa servizi AI cloud né una demo a scadenza.

## Camere nel pannello Klipper

Aggiungi in Fluidd una camera di tipo pagina HTTP/iframe con l'indirizzo di
PrintWatch raggiungibile dal browser e `?embed=camera` alla fine. La vista è compatta:
immagine grande, tasti piccoli, **Dati e filamento** in evidenza. Per un telefono
usa il tuo indirizzo privato Tailscale, non il localhost del computer.

## Filamento

Il sensore Klipper indica presenza/assenza o movimento, non il peso rimasto.
Per la stima, **Imposta bobina** richiede i grammi effettivamente disponibili adesso,
esclusa la bobina vuota. Il consumo successivo aggiorna il contatore. Il software
confronta il residuo con il fabbisogno previsto dallo slicer e segnala quantità bassa
o insufficiente. L'autonomia è indicativa; non sostituisce un sensore o una bilancia.

## Telefono

L'accesso privato opzionale con Tailscale si prepara con:

```sh
.venv/bin/python -m printwatch.remote_setup --enable-serve
```

Il comando ricava dal tuo account il nome del tuo computer: non contiene nomi o IP
di altre persone. La vista AI remota è di sola lettura. Il pannello stampante
separato permette comandi reali, soltanto all'identità proprietaria configurata.
Vedi prerequisiti e comportamento nel [README completo](README.md).

## Stato del progetto

Prima versione sperimentale: test automatici disponibili, prova reale eseguita su
macOS Apple Silicon. Installazione Intel predisposta ma non ancora verificata su
hardware reale. Linux/Windows non sono ancora verificati end to end. Non è dimostrata
una maggiore precisione rispetto al modello originale e non è stato effettuato
un nuovo addestramento. Prima di abilitare azioni automatiche servono prove sul
proprio materiale, illuminazione, telecamere e tipi di guasto.

La cartella `data/`, i modelli, i log, le immagini e le configurazioni locali non
vanno pubblicati. Il repository include regole `.gitignore` e nessun dato reale.

## Uso continuativo

Se il computer che esegue PrintWatch va in stop o si spegne, l'analisi si ferma e
il collegamento remoto smette di funzionare. Tailscale non tiene acceso il server.
Per usarlo stabilmente installalo sul computer destinato a rimanere acceso,
configura il risparmio energetico e verifica l'avvio automatico dopo il login.
Un indirizzo IP fisso della stampante non risolve lo stop del computer.
La [guida al funzionamento continuativo](DEPLOYMENT.md) elenca le prove necessarie.

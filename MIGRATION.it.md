# Da PrintWatch e LayerSentra a LayerScan

Il progetto si chiama ora **LayerScan** (in precedenza PrintWatch e LayerSentra). Il tema Dot, i dati e il
modello restano gli stessi. Il vecchio nome era già utilizzato da un altro prodotto
nel settore del monitoraggio delle stampe 3D; questo progetto è indipendente.

Il repository diventa https://github.com/Gregalterego/LayerScan. I vecchi URL GitHub
vengono reindirizzati dalla piattaforma. Le release precedenti e la cronologia
conservano i nomi storici: non vengono cancellate o riscritte.

## Installazioni esistenti

Non rinominare manualmente la cartella di un server in funzione. Un vecchio
LaunchAgent può contenere percorsi assoluti, il Python dell'ambiente virtuale e
`python -m printwatch.app`. Il comando storico continua a funzionare grazie al
piccolo modulo di compatibilità che avvia `layerscan.app`.

`update-macos.command` riconosce `~/Applications/LayerScan`, `~/Applications/LayerSentra` e
`~/Applications/PrintWatch`. Crea un backup del codice, conserva configurazione,
modelli, contatori, storico e identità remota e mantiene il percorso/servizio attuali.
Rifiuta l'aggiornamento durante una stampa attiva o in pausa. Se esistono più
installazioni, indicare esplicitamente la cartella con `LAYERSCAN_HOME` (anche il precedente `LAYERSENTRA_HOME` è accettato).
Nuove installazioni usano il nome LayerScan e il modulo `layerscan`.

Le app mantengono temporaneamente gli identificativi tecnici di sviluppo usati
nelle prime versioni per Android e Apple: cambiarli creerebbe app separate e perderebbe le preferenze.
Su Windows il nuovo nome usa una cartella delle preferenze separata: reinserire gli
indirizzi del server nella nuova app. I dati del server non vengono spostati o cancellati.
Nome visibile, marchio, icone, pacchetti e codice client sono LayerScan. Prima di
una distribuzione negli store scegliere identificativi definitivi sotto il proprio
controllo. La firma Android di debug continua a poter richiedere una nuova
installazione se cambia il sistema di compilazione.

Gli header tecnici precedenti vengono accettati come alias per permettere ai
client e proxy già configurati di funzionare. Non cambia l'autenticazione e non
vengono esposti nuovi indirizzi, password o token. I nuovi client inviano anche
l'alias precedente per poter leggere server ancora da aggiornare.

Il nome della camera memorizzato in Fluidd è un'impostazione locale separata:
se esiste una voce «PrintWatch AI», rinominarla in «LayerScan AI» mantenendo ID,
URL, altre camere e selezione. Il nome host Tailscale del proprio computer non
dipende dal nome del progetto e non deve essere modificato per questo passaggio.

Il cambio di nome non installa automaticamente il nuovo codice su un server remoto.

Su Linux un servizio precedente può conservare utente, percorso e nome storici:
il comando di compatibilità continua a funzionare dopo aver aggiornato il codice.
Non attivare contemporaneamente due servizi sullo stesso server.

Anche `python -m layersentra.app` rimane disponibile come alias del nuovo server.
I vecchi pacchetti già pubblicati non vengono riscritti: le nuove compilazioni usano LayerScan.

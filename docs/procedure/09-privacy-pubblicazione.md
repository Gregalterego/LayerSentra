# Pubblicazione senza dati dell’installazione

Questa sezione descrive il criterio usato per preparare la guida pubblica. La documentazione viene riscritta usando segnaposto, non pubblicando la conversazione o ripulendo soltanto i nomi dei file.

## Esclusioni

Non pubblicare:

- IP LAN/VPN effettivi, host privati o nomi della rete;
- login, email, nomi utenti e percorsi delle cartelle personali;
- ID/password di programmi di controllo remoto;
- token API, cookie, intestazioni di autenticazione, chiavi private o sottoscrizioni push;
- configurazioni reali, `.env`, directory `data`, backup e report d’installazione;
- fotogrammi, registrazioni, file G-code personali e schermate di desktop;
- firmware e dump flash, che possono contenere sia componenti del produttore sia segreti del dispositivo;
- pesi di modelli o binari di terzi senza una decisione esplicita sui diritti di distribuzione.

Un hash o un nome di driver tecnico non è una password, ma pubblicarlo deve comunque servire alla riproduzione. Qui sono sufficienti il metodo e i dettagli del formato osservato.

## Controllo del contenuto

Preparare una cartella separata con una lista esplicita dei soli file da pubblicare. Controllare testo, nomi, metadati, link, file nascosti e cronologia Git. Cercare indirizzi, host VPN, percorsi assoluti personali, indirizzi email e firme di chiavi/token. Non copiare automaticamente tutti gli output di un’analisi.

`.gitignore` evita aggiunte accidentali future; non rimuove un segreto già commesso. Se un segreto è stato pubblicato, rimuoverlo dall’ultima versione non basta: revocare o ruotare la credenziale e gestire anche cronologia e copie secondo il servizio interessato.

## Esempi pubblici

Usare domini `.invalid` come `camera.example.invalid` e variabili documentate. I valori reali vanno inseriti soltanto nell’installazione privata. Non inserire password funzionanti negli esempi, neppure chiamandole «demo».

Questa guida è un insieme di procedure, non un installer universale: i componenti che dipendono dal dispositivo, il bootstrap compatibile, il modello e le credenziali devono essere forniti e verificati da chi la segue.

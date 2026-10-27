# Accesso ospite: telecamere, pausa e ripresa

Il download del codice non crea un link attivo. Il servizio ospite viene installato
separatamente dal monitor principale e ascolta soltanto su localhost finché non
si configura esplicitamente un proxy HTTPS pubblico.

Servizio separato dal pannello proprietario: espone soltanto immagini della camera
scelta, stato essenziale, pausa manuale e, solo se abilitata dal proprietario, ripresa. Non espone Fluidd,
G-code, configurazione, filamento, file, cancellazione o controllo AI.
La pausa usa l'indirizzo Moonraker già configurato sullo stesso host e viene
confermata rileggendo lo stato. Non è un arresto di emergenza e dipende dalla rete.

## Installazione da completare sul server autorizzato

Attendere il termine della stampa e usare la procedura di aggiornamento con backup,
senza rinominare installazione o ambiente virtuale. Il servizio proprietario e i
suoi URL restano privati. Non pubblicare le porte 7127, 7128 o Moonraker.

1. Scegliere un'origine HTTPS **dedicata** agli ospiti, senza percorsi.
2. Sul server, nella cartella del progetto, generare l'invito:
   `.venv/bin/python -m layersentra.guest --origin https://guest.example.org --camera secondary --hours 24`.
   Il dominio è un esempio e va sostituito solo con quello effettivamente configurato.
   Il comando crea `data/guest-access.json` con permessi 0600, senza modificare rete,
   servizi o stampante. Rifiuta di sovrascrivere un invito esistente.
3. Eseguire `layersentra.guest:create_app` come factory WSGI con un server di produzione
   (ad esempio Waitress), in ascolto **solo su 127.0.0.1:7130**. Il runtime WSGI e il
   servizio di avvio devono essere installati e verificati separatamente sull'host.
4. Predisporre il proxy/tunnel HTTPS verso **solo quel servizio**. Conservare l'Host
   pubblico nella richiesta, non creare fallback verso il pannello proprietario e
   non pubblicare intere directory. Non modificare le regole Serve già attive senza
   verificarne i conflitti. Funnel non è attivato da questo codice.
5. Verificare accesso senza invito negato, invito valido, scadenza/revoca, immagini
   aggiornate, rifiuto di tutti gli altri percorsi e isolamento dai pannelli privati.
6. Collaudare la pausa in una stampa di prova autorizzata. I test software non
   impartiscono movimenti o pause reali. Verificare quindi il link da rete esterna.

Il segreto dell'invito è nel frammento `#invite=…`, rimosso dalla barra dopo l'apertura;
non va pubblicato su GitHub, log, screenshot o servizi di anteprima. L'invito è una
credenziale trasferibile: chi lo riceve può vedere e mettere
in pausa. Non autentica l'identità personale del collega. Sessione HTTPS con cookie
Secure/HttpOnly/SameSite Strict, CSRF, scadenza massima otto ore e limite azioni.
Invito predefinito 24 ore, massimo sette giorni.

Per revocare, impostare localmente `enabled: false` nel file privato: anche le
sessioni già aperte vengono negate dalla richiesta successiva. Per ruotare,
revocare e rimuovere il vecchio file sul server, quindi generare un nuovo invito.
Non condividere il file privato. L'iMac deve rimanere acceso e connesso.

I test verificano isolamento, autenticazione, revoca, CSRF, rifiuto dei comandi PTZ, rate limit, frame scaduti e pausa tramite Moonraker simulato. La
compatibilità con un proxy pubblico e i dispositivi reali resta da collaudare.

La pagina ospite mostra i video, il grande pulsante rosso «PAUSA STAMPA» e, se
autorizzato, il piccolo pulsante verde «RIPRENDI STAMPA».
I comandi di movimento non sono disponibili neppure tramite chiamate dirette.

## Installazione separata su macOS

Sul computer proprietario con il server gia funzionante, `python tools/guest-install.py`
prepara `~/Applications/LayerSentraGuest`, un ambiente Python indipendente e il
LaunchAgent `local.layersentra.guest`. Usa il Python dell’installazione esistente
per eseguire lo script, se Python non e disponibile nel sistema. Rifiuta di
sovrascrivere un’installazione ospite presente o una porta 7130 occupata.
Il servizio principale non viene aggiornato o riavviato. La configurazione del
proprietario viene copiata solo sullo stesso computer, con permessi privati.
Il nome HTTPS viene ricavato dal client Tailscale locale; il servizio ospite usa
una porta HTTPS dedicata 10000, da verificare libera prima di configurare il tunnel.
Questo installatore prepara un invito di sette giorni, salvato in un file locale
con permessi 0600, e NON abilita Funnel ne modifica Serve.

`tools/guest-check.py`, eseguito con il Python dell’ambiente ospite, controlla il
video reale, l’accesso anonimo negato e i percorsi vietati. Non preme pausa e non
invia altri comandi alla stampante. La pausa reale va collaudata separatamente in
una prova autorizzata. La visibilita del pulsante e fissa in basso anche su telefono.

## Invito senza scadenza automatica

Solo dopo esplicita scelta del proprietario, `--permanent` genera un invito con
`expires_at: null`. Il link resta revocabile con `enabled: false` o cambiando
l’invito; non usare numeri infiniti o scadenze inventate. Le sessioni del browser
restano limitate a otto ore: basta riaprire lo stesso link completo per rientrare.
`tools/guest-permanent.py` aggiorna una installazione ospite esistente con backup,
conserva l’invito e riavvia soltanto il servizio ospite. Non attiva l’accesso Internet.
`tools/guest-publish.py` pubblica la sola porta ospite10000 dopo autorizzazione;
rifiuta di sostituire una porta gia configurata e verifica che443/8443restino private.
Su macOS avvia il programma Tailscale dal percorso canonico con maiuscole corrette.

## Pressione continua di cinque secondi e seconda camera

Entrambi i pulsanti richiedono una pressione continua di almeno cinque secondi.
Il riempimento e il conto alla rovescia mostrano l’avanzamento. Rilasciare, uscire
con il puntatore dal pulsante, cambiare scheda o perdere il collegamento annulla
la pressione. Sono supportati mouse, tocco e tastiera (Spazio/Invio tenuti premuti).
Un tocco breve non esegue comandi.

Il server emette un permesso monouso legato alla sessione e all’azione: prima di
cinque secondi, dopo venti secondi, dopo annullamento o al riutilizzo viene negato.
Lo stato reale della stampante viene verificato di nuovo immediatamente prima
del comando. La ripresa usa soltanto il lavoro gia in pausa, senza avviare file.

La ripresa ospite richiede `can_resume: true` nel file privato: e negata per default.
Le camere autorizzate sono definite da `camera_ids: ["primary", "secondary"]`.
Non aggiungere URL nel client; ogni immagine viene letta dal servizio proprietario.
Se una camera non risponde, l’altra resta visibile. Nessun comando PTZ e disponibile.

`tools/guest-update-hold.py --enable-resume` aggiorna una installazione ospite
esistente dopo esplicita autorizzazione per entrambe le camere e la ripresa:
crea backup privati, conserva il link e la sua scadenza, riavvia solo il servizio
ospite e ripristina il codice precedente se i controlli falliscono. Il pannello
proprietario e Funnel non vengono modificati. I controlli di installazione non
mettono in pausa o riprendono la stampante reale.

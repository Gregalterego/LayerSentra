# Rotazione della telecamera: stato reale e procedura successiva

**La rotazione fisica della LSC non è stata collegata o verificata nel percorso documentato.** Le frecce nell’interfaccia non dimostrano che il server possa comandare i motori. Uno stream video, un invito nell’app o l’accesso al computer sulla stessa rete non concedono automaticamente una shell sulla camera.

## Prima verifica dalla stessa LAN

1. Ricavare l’indirizzo corrente della propria camera dalla configurazione privata o dall’inventario della propria rete.
2. Controllare in modo limitato i servizi pertinenti e leggere i loro messaggi iniziali.
3. Se esiste SSH/Telnet, usare soltanto credenziali note e autorizzate. Una porta aperta non è una sessione autenticata.
4. Se il servizio richiede una password sconosciuta, non fingere di aver ottenuto accesso; non provare liste di password.
5. Verificare se il servizio HTTP espone davvero comandi motori o caricamento file. La pagina video studiata non lo fa.

Nel caso studiato un servizio Telnet rispondeva con richiesta di login e password. Non è stata ottenuta una shell. Non si può dedurre che ogni camera abbia lo stesso servizio o la stessa autenticazione.

## Aggiornare la stessa microSD

È stato preparato un aggiornamento diagnostico, non ancora provato sul dispositivo nel percorso documentato:

1. Spegnere la telecamera, estrarre la scheda esistente e collegarla al computer.
2. Leggere il bootstrap effettivo; fare backup prima di modificarlo.
3. Mantenere i file video e la protezione HTTP globale già funzionanti.
4. Aggiungere un CGI diagnostico **fisso e in sola lettura**, che elenchi dispositivi motori, driver caricati, riferimenti nei descrittori del processo originale e strumenti disponibili.
5. Aggiornare il bootstrap affinché copi anche il nuovo CGI nel webroot temporaneo. Non aggiungere un’interfaccia che esegue comandi arbitrari ricevuti dalla richiesta.
6. Verificare la sintassi e le copie, espellere la scheda e reinserirla nella camera spenta.
7. Avviare, attendere il bootstrap e controllare prima il video, poi la pagina diagnostica autenticata.
8. Se qualcosa non funziona, ripristinare il bootstrap dal backup e riavviare normalmente.

Il fatto che la SD sia dentro la camera non la rende accessibile come disco dal computer. Se manca un canale remoto autenticato per aggiornare i file, il passaggio fisico resta necessario. La fine di una stampa permette di pianificare manutenzione ma non elimina questo limite.

## Dal driver al movimento

Dopo l’inventario occorre analizzare la versione effettiva del driver, individuare un’interfaccia supportata e validare parametri e arresto. Non eseguire vecchi script con indirizzi di memoria fissi: una scrittura in `/proc/<pid>/mem` può corrompere il processo e non dimostra l’esistenza di un arresto affidabile.

Il contratto dell’adattatore predisposto nel monitor è:

- cinque direzioni ammesse: `left`, `right`, `up`, `down`, `stop`;
- URL del bridge configurati dall’amministratore, non ricevuti dal browser;
- POST JSON con `duration_ms: 200`;
- una richiesta alla volta, timeout limitati, nessun redirect;
- arresto autonomo del motore entro un secondo anche se client o rete scompaiono;
- Stop come comando aggiuntivo, non sostitutivo del limite autonomo.

Non basta impostare un flag `bridge_auto_stop` per dimostrare questa proprietà: va verificata sul bridge reale. Non inventare URL per rendere le frecce cliccabili. Mantenere disabilitato il PTZ finché i test non sono superati.

## Prove prima dell’abilitazione

Con spazio libero attorno alla camera verificare piccolo impulso su ogni asse, direzione, arresto normale e arresto dopo perdita del client. Controllare finecorsa e recupero dopo errore senza insistere sui limiti meccanici. Verificare video e risorse del dispositivo. Dopo un cambio inquadratura, ripetere la configurazione delle zone AI.

Questa guida non include firmware personalizzato, driver motori completo o compatibilità PTZ diretta certificata per la LSC.

# Verifica, aggiornamenti e ripristino

## Prima di aggiornare

- Annotare la revisione del codice e fare backup privato di configurazioni, database, contatore bobina e chiavi avvisi.
- Attendere una finestra di manutenzione con stampante ferma.
- Confrontare la versione di partenza prima di sostituire file: se nel frattempo sono cambiati, unire le modifiche invece di sovrascrivere.
- Non trasferire il backup privato nel repository pubblico.

Aggiornare il servizio non significa aggiornare il firmware della stampante o della camera. Nel percorso documentato gli aggiornamenti del monitor sono stati fatti separatamente e con possibilità di ripristino.

## Verifica dopo l’aggiornamento

| Controllo | Risultato atteso |
|---|---|
| Dashboard | Si apre con autenticazione corretta |
| Stampante | Stato coerente con Fluidd e dati aggiornati |
| Video | Immagini recenti da entrambe le sorgenti |
| AI | Modello pronto; osservazione; stato attivo/fermo desiderato |
| Peso bobina | Modulo disponibile, valori persistenti e nessun dato fittizio |
| Fabbisogno | Calcolato soltanto con metadati validi |
| Avvisi | Registro disponibile; prova sul destinatario da verificare |
| PTZ | Disabilitato se il bridge non è stato validato |

Testare il salvataggio peso in un ambiente isolato con stampante simulata; in produzione usare soltanto una misura reale. Per provare la sottrazione tara senza alterare dati è possibile compilare il modulo e annullare.

## Problemi frequenti

| Sintomo | Verifica utile |
|---|---|
| Peso non cliccabile da remoto | Versione frontend/backend e autorizzazione dedicata; non togliere tutti i controlli remoti |
| «Sconosciuto» a stampante ferma | File e metadati possono non essere disponibili |
| «Sufficiente» senza fabbisogno | Correggere il criterio: fabbisogno numerico richiesto |
| Video app LSC sì, monitor no | Il servizio video locale è separato da quello cloud |
| HTTP 401 dalla camera | Credenziali private coerenti, senza inserirle nell’URL |
| HTTP 409 acquisizione | Evitare client concorrenti; controllare il lock |
| HTTP 503 o immagini scadute | Alimentazione, Wi-Fi, SD, buffer, lettore e FFmpeg |
| Nessuna analisi in standby | Comportamento previsto del monitor durante inattività |
| Avvisi presenti nel registro ma non sul telefono | Iscrizione, permessi, prova a schermo bloccato e server acceso |
| Telnet aperto ma password richiesta | Non è accesso shell ottenuto |

Un lock di acquisizione rimasto dopo un arresto brusco può durare fino al riavvio della camera. Non cancellarlo mentre un altro processo acquisisce. Prima di riavviare registrare privatamente lo stato utile alla diagnosi.

## Ripristino

Per il monitor: fermare il servizio con il suo meccanismo normale, ripristinare i file della revisione precedente e riavviare, poi rifare i controlli. Non sostituire una configurazione più recente senza confrontarla. Verificare l’AI dopo il riavvio: l’avvio prudente può riportarla ferma e in osservazione.

Per la microSD: spegnere la camera, ripristinare lo script precedente dal backup e riavviare con la scheda inserita. Non rimuovere la scheda a caldo. Nessun flash è necessario per ripristinare un semplice bootstrap temporaneo se non sono state effettuate altre modifiche persistenti.

## Passaggio a un altro computer

Trasferire il codice e una guida priva di segreti. Migrare separatamente e privatamente i dati strettamente necessari. Ricreare dipendenze e percorsi del servizio sul nuovo host, configurare l’accesso privato e testare ogni sorgente. Un URL o una sessione remota del vecchio computer non si trasferiscono automaticamente. Non confondere il nuovo computer usato per amministrare con quello che deve eseguire il monitor continuativamente.

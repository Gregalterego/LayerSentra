# Accesso privato e avvisi sul telefono

## Collegamento remoto

Il server deve raggiungere la LAN della stampante. Il telefono deve raggiungere il server tramite un accesso autenticato, per esempio una VPN privata con proxy HTTPS. Non pubblicare direttamente Moonraker o la porta HTTP della telecamera.

1. Configurare la propria rete privata seguendo la documentazione del fornitore.
2. Usare gli strumenti di configurazione remota della release del monitor, se disponibili; controllare prima che cosa modificano.
3. Configurare l’identità proprietaria privata e l’hostname della propria installazione.
4. Verificare che il backend accetti le intestazioni d’identità soltanto dal proxy locale fidato e per l’host previsto.
5. Provare l’accesso con l’utente proprietario e il rifiuto per un’identità diversa.
6. Verificare separatamente la dashboard e il pannello completo della stampante: quest’ultimo può inviare comandi reali.

Non basta inoltrare una porta o fidarsi di un’intestazione che qualsiasi client può inviare. I file con login, hostname, chiavi, token e configurazione remota restano locali. Non pubblicare gli indirizzi effettivi nei ticket.

## Avvisi previsti

Il percorso implementato include pausa, ripresa, fine stampa, annullamento, errore, perdita di collegamento e stime di filamento basso o insufficiente. Sono previsti anche avvisi per telecamera senza immagini valide durante stampa. Le transizioni devono essere confermate e le interruzioni non devono produrre messaggi ripetuti a ogni ciclo.

Gli avvisi informano: non devono diventare implicitamente comandi alla stampante. Il messaggio push del percorso studiato è generico, senza immagini e nomi dei file di stampa.

## Attivazione per dispositivo

1. Aprire il monitor con il collegamento privato attivo.
2. Aprire «Avvisi» sul **telefono che deve riceverli**, non soltanto sul computer.
3. Usare il pulsante di attivazione/sincronizzazione e concedere il permesso del browser.
4. Inviare una prova e verificare la ricezione sia con pannello aperto sia a schermo bloccato.
5. Verificare poi almeno una transizione reale controllata senza interrompere una stampa per il solo test.

Su iPhone può essere necessario aggiungere la web app alla schermata Home da Safari e aprirla dall’icona. Compatibilità, impostazioni del sistema e requisiti variano: consultare le fonti ufficiali correnti riportate sotto.

L’accettazione da parte del servizio push non prova la consegna al telefono. Un evento nel registro locale non prova che il telefono sia iscritto. Nel percorso documentato la ricezione finale a schermo bloccato resta da validare.

## Gestione del server

Il computer deve restare acceso; Internet e il servizio push devono essere disponibili. Il server genera gli avvisi anche con dashboard chiusa, ma non quando è spento. Conservare chiavi VAPID e sottoscrizioni in file privati. La registrazione del dispositivo deve avere controlli di identità, origine e token e limitare i servizi push ammessi.

Dopo un aggiornamento verificare avvio del componente avvisi, assenza di duplicati e iscrizioni esistenti. Non cancellare o rigenerare le chiavi senza un motivo: potrebbe rendere necessaria una nuova iscrizione dei dispositivi.

## Fonti ufficiali da consultare

- [Documentazione API Moonraker](https://moonraker.readthedocs.io/en/latest/external_api/introduction/).
- [Documentazione Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve).
- [WebKit: Web Push per web app su iOS/iPadOS](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/).
- [Documentazione Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API).

Questi link sono riferimenti esterni da ricontrollare per la propria piattaforma; la guida non certifica la compatibilità di ogni versione futura.

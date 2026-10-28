# Analisi AI e controlli

## Attivazione prudente

1. Procurarsi un modello compatibile con input, output e categorie attesi dal programma; leggere la documentazione della release.
2. Installarlo privatamente nel percorso configurato. Non includere pesi nel repository senza verificarne licenza e provenienza.
3. Controllare che lo stato del modello diventi «Pronto» senza errori.
4. Impostare zona di analisi e maschere sulla propria inquadratura. Escludere aree non pertinenti.
5. Usare «Avvia AI» in sola osservazione e confrontare eventi e immagini durante stampe reali.
6. Provare «Ferma AI»: deve fermare l’analisi, lasciando disponibile il video e senza inviare comandi alla stampante.

Il monitor analizza durante una stampa attiva con dati e fotogrammi validi. «AI in attesa» con stampante in standby non significa necessariamente guasto.

## Conferme e accuratezza

Non trattare un singolo frame come prova di errore. Usare la conferma temporale prevista dal programma, azzerandola per immagini scadute, cambio file, ripresa o variazioni rilevanti dell’inquadratura. Il punteggio del modello non è una probabilità calibrata di guasto. Il modello pronto, un riquadro o un evento nel registro non dimostrano accuratezza sulle proprie stampe.

La soglia corretta dipende da materiale, illuminazione, colore, geometria e camera. La procedura non include un nuovo addestramento e non certifica il rilevamento di tutti i difetti.

## Comandi remoti

L’implementazione provata separa avvio/arresto AI, movimento camera, avvisi e configurazione generale. L’accesso del proprietario e il controllo dell’origine della richiesta restano necessari anche quando si usano token dedicati. Non divulgare una risposta API che contiene questi token.

Avvio e arresto della sola osservazione non devono abilitare implicitamente la pausa automatica. Dopo un aggiornamento verificare che l’AI sia tornata allo stato desiderato e che la modalità sia ancora osservazione.

## Azioni sulla stampante

La pausa automatica non è necessaria per riprodurre il monitoraggio descritto. Se si decide successivamente di implementarla o abilitarla, servono prove specifiche, conferma dello stato stampante immediatamente prima dell’azione e verifica del risultato. Non riarmare automaticamente dopo un errore non chiarito. Questa guida non presenta tale funzione come validata per proteggere una stampa senza supervisione.

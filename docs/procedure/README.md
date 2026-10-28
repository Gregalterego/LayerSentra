# Guida pratica: monitor di stampa, Fluidd e telecamera LSC / Anyka

Questa guida raccoglie il percorso seguito per integrare un monitor locale di stampa con Klipper/Moonraker, Fluidd, una seconda telecamera LSC/Anyka, analisi AI, stima filamento e avvisi. È una documentazione tecnica riproducibile con i propri dispositivi e le proprie configurazioni, non un backup di un’installazione personale.

Il progetto è stato chiamato PrintWatch nelle prime prove; il repository e i pacchetti successivi possono usare un nome diverso. Usare i nomi di moduli, i comandi e le dipendenze della versione effettivamente scaricata. Le prove storiche descritte qui non certificano automaticamente ogni revisione successiva del repository.

## Percorso di lettura

1. [Architettura, prerequisiti e stato verificato](01-architettura.md).
2. [Installazione del monitor e dati da Moonraker](02-monitor-fluidd.md).
3. [Telecamera LSC: analisi statica, microSD e video](03-telecamera-lsc.md).
4. [Analisi AI e controlli](04-analisi-ai.md).
5. [Peso filamento, consumo e calcoli](05-filamento.md).
6. [Accesso privato e notifiche sul telefono](06-accesso-avvisi.md).
7. [Rotazione PTZ e diagnostica: lavoro ancora aperto](07-ptz-diagnostica.md).
8. [Backup, verifica e risoluzione problemi](08-verifica-ripristino.md).
9. [Cosa escludere da una pubblicazione](09-privacy-pubblicazione.md).

## Cosa è stato ottenuto e cosa manca

| Funzione | Evidenza del percorso documentato |
|---|---|
| Video principale e seconda LSC nel monitor | Provati su un’installazione reale |
| Pannello Fluidd e vista camera incorporata | Provati |
| Pulsanti avvio/arresto AI in osservazione | Provati |
| Modello pronto e registro rilevamenti | Osservati; accuratezza non certificata |
| Peso modificabile e schede filamento interattive | Installati nella revisione sperimentale descritta; apertura e calcolo provati |
| Salvataggio peso e conteggio consumo | Test isolati con dati controllati; nessun peso inventato inserito nel sistema reale |
| Registro avvisi pausa/ripresa | Eventi osservati |
| Ricezione push su telefono bloccato | Da validare sul dispositivo destinatario |
| Frecce PTZ | Interfaccia e adattatore predisposti; motori non collegati né provati |
| Coesistenza completa con app Tuya/LSC | Non dimostrata con una prova prolungata |
| Firmware personalizzato della telecamera | Non prodotto e non installato |

Le istruzioni relative a funzionalità sperimentali descrivono anche i criteri per implementarle e verificarle. Non presumere che la propria release includa tutte le modifiche della revisione provata: confrontare API, interfaccia e documentazione della release prima di aggiornare.

## Esempi senza dati personali

Tutti gli host riportati sono segnaposto riservati agli esempi: `printer.example.invalid`, `camera.example.invalid`, `monitor.example.invalid`. Devono essere sostituiti **solo nei file privati della propria installazione**. `localhost` indica sempre il dispositivo sul quale viene aperto. I numeri di porta sono convenzioni software degli esempi, non indirizzi di una rete reale.

Non sono inclusi indirizzi personali, account di accesso remoto, credenziali, token, configurazioni reali, registrazioni, firmware del produttore, dump flash o pesi dei modelli AI.

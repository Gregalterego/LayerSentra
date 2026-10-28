# Movimento della telecamera LSC

Le frecce sono disponibili nel pannello web e nelle app. Restano disabilitate finché
il server non dispone di un collegamento PTZ verificato. Un invito LSC, uno stream
RTSP o un ponte che fornisce immagini non sono comandi di movimento.

**Non è ancora stata verificata una compatibilità PTZ diretta con la LSC Dualband
Indoor 2.** Questo progetto include il client per un bridge HTTP locale; non include
un firmware LSC, un driver motori, un client Tuya cloud o un servizio ONVIF validato.
Non impostare URL inventati e non usare gli endpoint della stampante per muovere la camera.

## Contratto del bridge

Un amministratore può configurare cinque URL HTTP/HTTPS privati per `left`, `right`,
`up`, `down`, `stop` in `data/ptz.json`. Il file non è pubblicato. Ogni richiesta è un
POST JSON con `duration_ms: 200`; deve rispondere 200 o 204.

Ogni movimento deve essere un impulso limitato e il bridge **deve arrestare da solo
il motore entro un secondo**, anche se LayerScan, la rete o il client si interrompono.
Il pulsante Stop è aggiuntivo: non sostituisce il limite autonomo del bridge.
Non collegare direttamente API che avviano una rotazione continua senza arresto autonomo.
LayerScan non può verificare da solo che il bridge rispetti tale requisito.

Configurazione di esempio, da adattare soltanto dopo aver verificato il bridge:

```json
{
  "enabled": false,
  "camera_id": "secondary",
  "bridge_auto_stop": true,
  "commands": {
    "left": "http://127.0.0.1:7140/left",
    "right": "http://127.0.0.1:7140/right",
    "up": "http://127.0.0.1:7140/up",
    "down": "http://127.0.0.1:7140/down",
    "stop": "http://127.0.0.1:7140/stop"
  }
}
```

La porta 7140 è un esempio: nessun servizio su tale porta viene installato dal
progetto. Impostare `enabled: true` solo dopo la validazione del bridge e della
camera, con spazio libero per la rotazione. La posizione della camera cambia ROI,
maschere e illuminazione: controllare di nuovo i parametri AI dopo averla mossa.

Il server accetta solo cinque direzioni predefinite, impedisce comandi simultanei,
non segue redirect e non accetta URL inviati dal browser. L'accesso remoto usa un
token distinto dal controllo dell'analisi e dalla configurazione generale.

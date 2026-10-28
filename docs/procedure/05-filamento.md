# Filamento: peso, dati reali e risultati calcolati

## Da dove arrivano i numeri

| Informazione | Origine |
|---|---|
| Presenza o movimento filamento | Oggetto sensore esposto da Klipper |
| Metri consumati nella stampa | `print_stats.filament_used`, convertito da mm |
| Lunghezza totale prevista | Metadati del G-code, se disponibili |
| Massa totale prevista e materiale | Metadati estratti dal file, se disponibili |
| Grammi disponibili sulla bobina | Peso netto inserito dall’utente |
| Residuo e sufficienza | Calcoli basati sui dati precedenti |

Fluidd non pesa la bobina. Un sensore di presenza non misura grammi residui e un sensore disabilitato non protegge dall’esaurimento.

## Inserire la bobina

Nella revisione sperimentale con il modulo interattivo:

1. Aprire «Dati e filamento», poi «Inserisci / aggiorna peso» o la scheda della bobina.
2. Inserire i grammi netti effettivamente disponibili **adesso**. In alternativa selezionare peso totale meno tara e inserire entrambe le misure.
3. Controllare diametro, densità del materiale e soglia di avviso.
4. Salvare e attendere l’aggiornamento dei valori.
5. Riaprire la pagina e controllare che il valore sia persistito, senza contare due volte il consumo già avvenuto.

Esempio puramente numerico: 1.200 g complessivi − 250 g di bobina vuota = 950 g di filamento. Non usare una tara generica per una bobina diversa. Un valore iniziale di densità non è un riconoscimento automatico del materiale.

Il diametro e la densità devono conservare i decimali necessari: per esempio 1,75 mm non va presentato come 1,8 mm nelle impostazioni tecniche.

## Calcoli

Con lunghezza `L` in mm, diametro `d` in mm e densità `ρ` in g/cm³:

`massa_g = L × π × (d / 2)² × ρ / 1000`

Fabbisogno residuo in lunghezza:

`max(0, lunghezza_totale_file − lunghezza_consumata)`

Se i metadati forniscono massa e lunghezza totali valide, si può usare il rapporto massa/lunghezza del file per il fabbisogno. In assenza della massa, la conversione geometrica dipende dalla densità configurata. Il contatore della bobina provato usa la conversione configurata per sottrarre il consumo osservato: può differire dalla stima dello slicer.

`bobina_residua = peso_netto_inserito − consumo_osservato_successivo`

L’autonomia indicativa usa il consumo medio recente, dopo almeno 30 secondi osservati durante stampa; il percorso provato mantiene una finestra fino a cinque minuti. Non è un orario garantito.

## Schede cliccabili

- **Consumato:** dettaglio della lettura Klipper.
- **Previsto per finire:** dati del file e fabbisogno residuo.
- **Stima sulla bobina:** modulo per inserire o correggere il peso.
- **Disponibilità:** confronto e spiegazione del risultato.

Con una stampa assente o metadati insufficienti il fabbisogno deve rimanere non disponibile. Non mostrare «Sufficiente» solo perché `spool_insufficient` è falso: richiedere anche un fabbisogno numerico valido. Se la stampante non risponde, evidenziare i dati scaduti.

## Requisiti per abilitare il salvataggio remoto

Le prime versioni nascondevano il pulsante nella vista remota. La correzione sperimentale aggiunge un’API dedicata `/api/spool` con token separato e soli quattro campi: `remaining_g`, `diameter_mm`, `density_g_cm3`, `low_warning_g`. Non consiste nel rimuovere il blocco generale di tutte le richieste remote.

Chi implementa la correzione deve mantenere autenticazione proprietario, controllo origine, verifica token e validazione numerica. Rifiutare valori negativi, booleani al posto di numeri, valori non finiti e campi aggiuntivi. Il token bobina non deve autorizzare configurazione generale, AI o PTZ. Salvare privatamente e in modo atomico; leggere un contatore aggiornato al momento dell’impostazione per non sottrarre di nuovo il passato.

Test richiesti: utente errato, origine errata, token mancante, campi inattesi, input non valido, salvataggio valido, consumo successivo, lettura ripetuta senza doppia sottrazione, cambio/reset contatore e persistenza dopo riavvio. Conservare la modalità AI precedente quando si salva la bobina.

## Limiti

Il residuo è una stima contabile, non una bilancia. Estrusioni manuali fuori stampa non sono conteggiate nel percorso documentato. Stampe durante lo spegnimento del monitor, reset dei contatori o sostituzioni di bobina richiedono riconciliazione del peso. Non applicare automaticamente il consumo di una bobina a una nuova bobina senza ristabilire il valore iniziale.

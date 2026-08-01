# Changelog

Tutte le modifiche significative a questo progetto saranno documentate in questo file.

## [2.5.0] — 2026-08-01

### Aggiunto
- **Guida in linea**: nuova pagina "Guida" nell'app con manuale completo d'uso, organizzato in sezioni (Introduzione, Registrazione movimenti, Estratto conto, Prenotazioni & Ospiti, Scadenzario, Resoconto & Analisi, Ricevute & Pagamenti, Categorie, Backup & Ripristino, FAQ & Suggerimenti).
- **Carica Estratto Conto**: nuova pagina per importare automaticamente le transazioni da file Excel (`.xlsx`, `.xls`) o CSV (`.csv`).
- **Categorizzazione automatica**: funzione `auto_categorizza()` che riconosce automaticamente la voce contabile in base alla descrizione (bollette, affitti, stipendi, F24, tasse di soggiorno, internet, commissioni OTA, ecc.).
- **Rilevamento duplicati automatico**: durante l'importazione dell'estratto conto, le transazioni già presenti nel database (stessa data e importo) vengono deselezionate automaticamente.
- **Analisi estratto conto**: anteprima del file, selezione guidata delle colonne (data, descrizione, importo singolo o due colonne entrate/uscite), riepilogo entrate/uscite/saldo, saldo iniziale/finale con verifica di quadratura, totali per voce e grafici (suddivisione spese e dettaglio utenze).
- **Modifica e validazione pre-importazione**: tabella editabile per modificare categorie, metodi di pagamento, descrizioni o deselezionare righe prima del salvataggio.
- **Dipendenza `openpyxl`**: aggiunta a `requirements.txt` per la lettura dei file Excel.
- **Gestione ambiente dev**: nuova funzione `carica_secrets_ambiente()` che legge le credenziali da `dev_secrets.toml` quando `APP_ENV=dev`, con fallback a `.streamlit/secrets.toml` o `.env`.
- **Avvio locale migliorato**: `run_local.py` ora forza l'encoding UTF-8 su Windows, imposta l'ambiente dev, apre automaticamente il browser su `http://localhost:8501` e usa la porta 8501 esplicita.
- **`avvia_app.bat` semplificato**: ora delega a `run_local.py` (gestione encoding, dipendenze e credenziali).

### Modificato
- **Navigazione**: aggiunta la voce "Guida" nella barra laterale.
- **`.gitignore`**: sostituita la voce `demo_secrets.toml` con `dev_secrets.toml`.
- **Rimozione file demo**: eliminati `DEMO_README.md`, `demo_setup.sql` e `seed_demo.py` (non più necessari).

## [2.4.0] — 2026-07-31


### Aggiunto
- **Backup & Ripristino**: nuova pagina dedicata per creare backup manuali completi dei dati (transazioni, categorie e scadenze) in file JSON scaricabili.
- **Ripristino da backup**: possibilità di selezionare un backup esistente e ripristinare tutti i dati su Supabase, con conferma obbligatoria per evitare operazioni accidentali.
- **Cartella `backups/`**: i file di backup vengono salvati automaticamente in una cartella dedicata, creata all'avvio dell'app.
- **Avvio locale semplificato**: nuovo script `run_local.py` che verifica automaticamente le dipendenze e le credenziali Supabase, poi avvia l'app su `http://localhost:8501`.
- **File `avvia_app.bat`**: doppio clic per avviare l'app su Windows, con verifica automatica del file `.env` e delle dipendenze.
- **File `.env.example`**: template di riferimento per la configurazione delle credenziali Supabase.
- **Modulo Prenotazioni & Ospiti**: nuova pagina per la gestione delle prenotazioni del B&B con registrazione ospiti, check-in/check-out, calcolo automatico dei pernottamenti, camere e canali di prenotazione.
- **Tracciamento tasse di soggiorno**: campo dedicato per registrare la tassa di soggiorno per ogni prenotazione, con registrazione automatica come uscita in contabilità.
- **Gestione commissioni OTA**: campo per registrare le commissioni trattenute dai canali (Booking, Airbnb, Expedia), con registrazione automatica come uscita in contabilità.
- **Registrazione automatica in contabilità**: al completamento di una prenotazione, l'importo del soggiorno viene registrato come entrata (voce "Fatturato / Vendite"), la commissione e la tassa di soggiorno come uscite.
- **Report fiscali**: nuovo tab in "Resoconto & analisi" con riepilogo mensile e trimestrale di entrate/uscite/saldo, grafico andamento mensile ed export del report per la dichiarazione fiscale.
- **Tabella Supabase `prenotazioni`**: aggiornato lo script `supabase_setup.sql` per la creazione della nuova tabella nel database backend.

### Corretto
- **Errore di sintassi in `app.py`**: rimossi i marcatori di conflitto di merge Git (`<<<<<<< HEAD`, `=======`, `>>>>>>>`) rimasti nel file che causavano `SyntaxError: invalid syntax` all'avvio.
- **Duplicazione codice**: risolte le righe duplicate nella funzione `aggiungi_transazione` e normalizzato correttamente il metodo di pagamento in `registra_pagamento_scadenza`.
- **Crash all'avvio senza `secrets.toml`**: aggiunta la funzione `get_secret()` che legge `st.secrets` senza sollevare errori quando il file non esiste, evitando `StreamlitSecretNotFoundError` che bloccava l'avvio dell'app.
- **Crash login senza `secrets.toml`**: la lettura degli utenti (`UTENTI`) da `st.secrets` ora è protetta da `try/except`, con fallback automatico alle credenziali predefinite `admin/admin`.

### Modificato
- **Navigazione**: aggiunte le voci "Prenotazioni & Ospiti" e "Backup & Ripristino" nella barra laterale.
- **`.gitignore`**: aggiunta la cartella `backups/` per escludere i file di backup dal versionamento.
- **README**: aggiornata la documentazione con le istruzioni per l'avvio locale, la nuova funzionalità di backup e il modulo prenotazioni.
- **`avvia_app.bat`**: riscritto con struttura più robusta (istruzioni `goto` invece di blocchi annidati), supporto completo per `secrets.toml`, gestione automatica delle dipendenze e corretta gestione dei caratteri accentati nel percorso (`chcp 65001`).
- **Configurazione credenziali**: l'app ora legge le credenziali Supabase e gli utenti di accesso dal file `.streamlit/secrets.toml`, con fallback al file `.env`.

## [2.3.0] — 2026-07-30

### Aggiunto
- **Metodi di pagamento estesi**: ora è possibile selezionare anche "Contanti" e "POS" nelle voci di registrazione movimento, nuova scadenza e pagamento scadenza.
- **Normalizzazione metodi**: i valori già presenti come "Contante" o "Pos" vengono convertiti automaticamente ai nuovi valori standard.

### Modificato
- **Archivio pagamenti e analisi**: il riepilogo per metodo di pagamento ora usa la lista condivisa e coerente di opzioni disponibili.

## [2.2.0] — 2026-07-28

### Aggiunto
- **Archivio ricevute**: nuova pagina dedicata per visualizzare, cercare e scaricare tutte le ricevute caricate, con filtri per tipo, anno e descrizione.
- **Archivio pagamenti**: nuova pagina con lo storico completo di tutti i pagamenti registrati, filtri avanzati (tipo, metodo, anno, persona), riepilogo entrate/uscite/saldo ed export CSV.
- **Salvataggio ricevute in sottocartelle**: le ricevute salvate localmente vengono ora organizzate in cartelle `anno/mese` per una migliore gestione.

### Modificato
- **Navigazione**: aggiornata la barra laterale con le nuove voci "Archivio ricevute" e "Archivio pagamenti".

## [2.1.0] — 2026-07-28

### Aggiunto
- **Modulo Scadenzario & Promemoria**: nuova sezione per la registrazione e gestione delle scadenze di entrate e uscite.
- **Promemoria automatici (7 giorni prima)**: banner di notifica globale nell'interfaccia dell'app che avvisa delle scadenze imminenti e scadute.
- **Supporto Scadenze Ricorrenti**: gestione della ripetizione (*Settimanale, Quindicinale, Mensile, Bimestrale, Trimestrale, Semestrale, Annuale*).
- **Automazione Saldo Contabile**: al click su "Segna come Pagato", registra automaticamente il movimento contabile in `transazioni` e aggiorna la scadenza successiva per le scadenze ripetute.
- **Tabella Supabase `scadenze`**: aggiornato lo script `supabase_setup.sql` per la creazione della nuova tabella nel database backend.

## [1.1.0] — 2026-07-27

### Aggiunto
- Migrazione da SQLite a **Supabase** come database backend
- File `.env` per la configurazione delle credenziali Supabase
- Script SQL `supabase_setup.sql` per creare le tabelle su Supabase
- Dipendenza `supabase-py` per l'integrazione con Supabase API REST
- Dipendenza `python-dotenv` per la gestione delle variabili d'ambiente
- File `CHANGELOG.md` per tracciare le modifiche
- File `README.md` con documentazione del progetto
- File `.gitignore` aggiornato per escludere `.env` e file sensibili

### Modificato
- `app.py` riscritto: tutte le funzioni CRUD ora comunicano con Supabase invece di SQLite
- Rimosse le dipendenze da `sqlite3` (non più necessario)
- Aggiunta colonna `created_at` nella visualizzazione della tabella transazioni

### Note
- I file delle ricevute rimangono salvati localmente in `ricevute_uploads/`
- Il database SQLite locale (`contabilita.db`) non viene più utilizzato
- Prima di avviare l'app, eseguire `supabase_setup.sql` nel SQL Editor di Supabase

## [1.0.0] — Versione iniziale

### Funzionalità
- App Streamlit per la gestione della contabilità personale
- Database SQLite locale
- Registrazione di entrate e uscite con categorie
- Caricamento e visualizzazione ricevute (PDF/immagini)
- Resoconto con filtri per data, totali e grafici
- Gestione categorie personalizzate
